import asyncio
import os
import yaml
import subprocess
import sys
import threading
import shutil
import re
from typing import List, Set, Optional

# Try importing SafeIO robustly (absolute then relative import) so the orchestrator
# works both when run as a package and when run from repo root during development.
try:
    from safe_io import SafeIO
except Exception:
    try:
        from ..safe_io import SafeIO
    except Exception:
        SafeIO = None  # type: ignore

from .planning import PlanningAndScaffoldingTask, ScaffoldingPlan
from .branch import BranchRunner
from .integration import IntegrationRunner
from .models import PlanAndCode
from .ast_utils import get_local_dependencies
from .testing import TestFailureAnalysisTask


class Improver:
    """The main orchestrator that runs the end-to-end improvement process."""
    def __init__(self, safe_io: SafeIO):
        self.safe_io = safe_io
        self._protected_files = set()
        try:
            content = self.safe_io.read('protected.yaml')
            if content:
                loaded = yaml.safe_load(content)
                if isinstance(loaded, list):
                    self._protected_files = set(loaded)
        except Exception:
            pass

    def _scan_project_files(self) -> List[str]:
        files = [os.path.join(root if root != '.' else '', f)
                 for root, _, fnames in os.walk('.')
                 if not any(p.startswith('.') for p in os.path.relpath(root, '.').split(os.sep))
                 for f in fnames if not f.startswith('.')]
        files.sort()
        return files

    async def _run_pytest(self) -> None:
        """Run pytest in a background thread and print results. Failures do not raise here.

        The routine prefers running pytest via `python -m pytest` using the current
        interpreter. If that fails, it will try importing pytest and invoking
        pytest.main. All blocking operations run in a thread via asyncio.to_thread.
        """
        print("\n[Improver] Running pytest (background)...")

        def _run_subprocess_pytest():
            try:
                # Run pytest from the project's root directory if available on SafeIO.
                cwd = getattr(self.safe_io, 'root_dir', os.path.abspath('.'))
                completed = subprocess.run(
                    [sys.executable, '-m', 'pytest', '-q'],
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                )
                stdout = completed.stdout or ""
                stderr = completed.stderr or ""
                rc = completed.returncode
                return rc, stdout, stderr
            except Exception as e:
                return 2, "", f"Subprocess invocation failed: {e}"

        def _run_import_pytest():
            try:
                cwd = getattr(self.safe_io, 'root_dir', os.path.abspath('.'))
                orig_cwd = os.getcwd()
                try:
                    os.chdir(cwd)
                    import pytest
                    # Running pytest.main is blocking; run inside thread.
                    rc = pytest.main(['-q'])
                    return rc, f'pytest.main() returned exit code {rc}', ''
                finally:
                    os.chdir(orig_cwd)
            except Exception as e:
                return 2, "", f"Import/invoke pytest failed: {e}"

        try:
            # Prefer subprocess approach; run it in a thread.
            rc, stdout, stderr = await asyncio.to_thread(_run_subprocess_pytest)

            # If subprocess failed to start pytest (rc != 0 and little output), try import fallback
            if rc != 0 and (not stdout) and (stderr and 'No module named' in stderr or not shutil.which('pytest')):
                rc2, out2, err2 = await asyncio.to_thread(_run_import_pytest)
                if out2 or err2:
                    stdout = stdout + out2
                    stderr = stderr + err2
                rc = rc2

            print("\n[pytest stdout]\n" + (stdout or "<no stdout>"))
            if stderr:
                print("\n[pytest stderr]\n" + stderr)
            print(f"[Improver] pytest finished with exit code: {rc}\n")
        except Exception as e:
            print(f"[Improver] Failed to run pytest: {e}")

        # If tests failed, attempt to analyze the failure using the TestFailureAnalysisTask
        if rc != 0:
            try:
                pytest_output = (stdout or '') + "\n" + (stderr or '')

                # Try to extract a failing test file path from pytest output
                def _extract_failing_test_path(output: str) -> Optional[str]:
                    # Look for patterns like 'path/to/file.py:123' which pytest often emits
                    m = re.search(r'(?m)([\w\./\\\-]+\.py):\d+', output)
                    if m:
                        candidate = m.group(1)
                        if os.path.exists(candidate):
                            return candidate
                        # try relative to cwd
                        rel = os.path.join(os.getcwd(), candidate)
                        if os.path.exists(rel):
                            return rel
                    # Look for 'FAILED some/path/to/test_file.py::test_name' style
                    m2 = re.search(r'(?m)^(FAILED|ERROR)\s+([^\s:]+\.py)', output)
                    if m2:
                        candidate = m2.group(2)
                        if os.path.exists(candidate):
                            return candidate
                    # Fallback: pick a test_*.py file in repo if present
                    for root, _, files in os.walk('.'):
                        for f in files:
                            if f.startswith('test_') and f.endswith('.py'):
                                return os.path.join(root, f)
                    return None

                test_path = _extract_failing_test_path(pytest_output)
                test_source = None
                if test_path:
                    try:
                        test_source = self.safe_io.read(test_path)
                    except Exception:
                        # best-effort; ignore failure to read
                        test_source = None

                # Create and invoke the analysis task
                analysis_task = TestFailureAnalysisTask(goal="Analyze pytest failure and determine cause")
                analysis_result = None
                try:
                    analysis_result = await analysis_task.execute(
                        pytest_output=pytest_output,
                        test_file_path=test_path,
                        test_source=test_source
                    )
                except TypeError:
                    # Some implementations may accept different kwarg names; try positional fallback
                    try:
                        analysis_result = await analysis_task.execute(pytest_output, test_path, test_source)
                    except Exception:
                        analysis_result = None

                if analysis_result is None:
                    print("[TestAnalysis] LLM returned no structured analysis.")
                else:
                    # analysis_result is a pydantic model instance (TestFailureAnalysis)
                    try:
                        verdict = getattr(analysis_result, 'verdict', None)
                        confidence = getattr(analysis_result, 'confidence', None)
                        explanation = getattr(analysis_result, 'explanation', None)
                        suggested_fix = getattr(analysis_result, 'suggested_fix', None)

                        print("\n[Improver] Test Failure Analysis Result:")
                        print(f"Verdict: {verdict or '<unknown>'} (confidence: {confidence or 'unknown'})")
                        if explanation:
                            print(f"Explanation: {explanation}")
                        if suggested_fix:
                            print(f"Suggested fix: {suggested_fix}")
                    except Exception:
                        print("[TestAnalysis] Received analysis but failed to read fields.")

            except Exception as e:
                print(f"[Improver] Failed to perform test failure analysis: {e}")

    async def run(self, goal, num_branches=3, iterations_per_branch=3):
        print(f"\nStarting workspace-aware improvement with goal: {goal}")
        file_tree = self._scan_project_files()
        if not file_tree:
            print("No files found in project directory.")
            return

        # Use PlanningAndScaffoldingTask to produce the scaffolding plan
        planning_task = PlanningAndScaffoldingTask(goal)

        # Validation and self-correction loop: generate plan and ensure existing_files_to_edit exist
        max_retries = 2  # allowed correction attempts
        attempt = 0
        error_context: Optional[str] = None
        plan: Optional[ScaffoldingPlan] = None

        def _path_variants(p: str) -> Set[str]:
            # Create plausible variants of a path to check for existence
            variants = set()
            variants.add(p)
            variants.add(os.path.normpath(p))
            if p.startswith('./'):
                variants.add(p[2:])
                variants.add(os.path.normpath(p[2:]))
            else:
                variants.add('./' + p)
                variants.add(os.path.normpath('./' + p))
            # also try stripped leading slashes
            variants.add(p.lstrip('./'))
            variants.add(os.path.normpath(p.lstrip('./')))
            return variants

        while True:
            # Try to pass error_context, but remain defensive if execute doesn't accept it
            try:
                plan = await planning_task.execute(file_tree=file_tree, error_context=error_context)
            except TypeError:
                # Fallback for LLMTask implementations that don't forward kwargs
                plan = await planning_task.execute(file_tree=file_tree)

            if not plan:
                print("PlanningAndScaffoldingTask returned no plan.")
                return

            # Log reasoning for visibility
            if getattr(plan, 'reasoning', None):
                print(f"\nLLM Reasoning from scaffolding plan:\n{plan.reasoning}\n")

            # Validate that files listed as existing actually exist (try normalized variants)
            missing = []
            for f in plan.existing_files_to_edit:
                found = False
                for variant in _path_variants(f):
                    if os.path.exists(variant):
                        found = True
                        break
                if not found:
                    missing.append(f)

            if not missing:
                break  # plan is valid

            # Build error message and retry
            missing_list = "\n".join(missing)
            error_message = (
                "The previous scaffolding plan references the following files that were not found in the repository:\n"
                f"{missing_list}\n\n"
                "Please either (a) update 'existing_files_to_edit' to refer only to files that currently exist in the project, "
                "or (b) if those files should be created as part of the scaffolding, list them under 'new_files_to_create'. "
                "Provide a corrected ScaffoldingPlan JSON object and include reasoning describing the changes."
            )

            attempt += 1
            print(f"Validation error in scaffolding plan detected (attempt {attempt}/{max_retries}). Missing files:\n{missing_list}\n")

            if attempt > max_retries:
                print("Exceeded maximum planning retries. Aborting improvement process due to invalid scaffolding plan.")
                return

            print("Re-running PlanningAndScaffoldingTask to correct plan based on error context...")
            error_context = error_message
            # loop will re-run planning with error_context

        # Create new files with empty content
        for new_file in plan.new_files_to_create:
            try:
                print(f"Creating new empty file as per scaffolding plan: {new_file}")
                self.safe_io.write(new_file, "")
            except PermissionError as e:
                print(f"Permission denied while creating new file {new_file}: {e}")
                return
            except Exception as e:
                print(f"Error while creating new file {new_file}: {e}")
                return

        # Combine existing_files_to_edit and new_files_to_create for full context
        combined_files = set(plan.existing_files_to_edit) | set(plan.new_files_to_create)

        # Filter out protected files for editing
        filtered_files = [f for f in combined_files if f not in self._protected_files]

        # Expand context by including local dependencies
        expanded_context: Set[str] = set(filtered_files)
        for file_path in filtered_files:
            try:
                deps = get_local_dependencies(file_path)
                expanded_context.update(deps)
            except Exception as e:
                print(f"Warning: Failed to get local dependencies for {file_path}: {e}")

        expanded_context_sorted = sorted(expanded_context)

        print(f"Files to improve (excluding protected): {sorted(filtered_files)}")
        print(f"Expanded context files after adding local dependencies: {expanded_context_sorted}")

        print(f"\n--- Starting multi-file improvement for files: {expanded_context_sorted} ---\nGoal: {goal}")

        runners = [BranchRunner(goal, self.safe_io, list(self._protected_files), i+1, iterations_per_branch).run(expanded_context_sorted) for i in range(num_branches)]
        results = await asyncio.gather(*runners)
        proposals = [dict(id=i+1, plan=r.reasoning, edits=r.edits) for i, r in enumerate(results) if r]
        if not proposals:
            print("\nResult: No successful proposals.")
            return

        integration = await IntegrationRunner(goal, self.safe_io).run(proposals)
        if not integration:
            print("\nResult: No integration result available.")
            return

        try:
            # Only read original content from existing files to edit, excluding protected
            original_files = [fp for fp in plan.existing_files_to_edit if fp not in self._protected_files]
            original = {fp: self.safe_io.read(fp) for fp in original_files}
        except Exception as e:
            print(f"Failed to read original files before applying changes: {e}")
            return

        # Check if any changes exist
        if not any(original.get(e.file_path) != e.code for e in integration.edits if e.file_path not in self._protected_files):
            print("\nResult: No changes detected after integration.")
            return

        print("\nApplying integrated changes...")
        try:
            for edit in integration.edits:
                if edit.file_path in self._protected_files:
                    print(f"Skipping write for protected file: {edit.file_path}")
                    continue
                self.safe_io.write(edit.file_path, edit.code)
        except PermissionError as e:
            print(f"Failed to write changes: {e}")
            return
        print(f"--- Finished multi-file improvement for files: {sorted(filtered_files)} ---")

        # After applying changes, run pytest in background. Do not let failures block the application.
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Schedule the coroutine on the current loop
                try:
                    asyncio.create_task(self._run_pytest())
                except Exception as e:
                    print(f"Warning: Failed to schedule pytest as an asyncio task: {e}")
                    # Fallback: run the coroutine in a background thread with its own loop
                    threading.Thread(target=lambda: asyncio.run(self._run_pytest()), daemon=True).start()
            else:
                # No running event loop; launch pytest in a background thread running its own event loop
                print("No running event loop; launching pytest in a background thread.")
                threading.Thread(target=lambda: asyncio.run(self._run_pytest()), daemon=True).start()
        except Exception as e:
            print(f"Warning: Failed to schedule pytest run: {e}")
