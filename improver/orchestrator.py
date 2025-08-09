import asyncio
import os
import yaml
import subprocess
import sys
import threading
import shutil
import re
import tempfile
from typing import List, Set, Optional, Tuple, Dict, Any

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
from .failure_log import should_halt_for_goal, increment_failure, clear_goal, clear_failure_for_test, get_failures_for_goal, quarantine_test, is_quarantined
# NOTE: Do NOT import TestFailureAnalysisTask at module import time to avoid
# triggering LLM provider or other heavy imports during module import. We'll
# import it dynamically when needed inside _run_pytest().


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

    async def _invoke_pytest_in_dir(self, cwd: str) -> Tuple[int, str, str]:
        """Invoke pytest in `cwd` and return (rc, stdout, stderr)."""
        def _run_subprocess_pytest(cwd_inner: str):
            try:
                completed = subprocess.run(
                    [sys.executable, '-m', 'pytest', '-q'],
                    capture_output=True,
                    text=True,
                    cwd=cwd_inner,
                )
                stdout = completed.stdout or ""
                stderr = completed.stderr or ""
                rc = completed.returncode
                return rc, stdout, stderr
            except Exception as e:
                return 2, "", f"Subprocess invocation failed: {e}"

        # Prefer subprocess approach; run in thread
        return await asyncio.to_thread(_run_subprocess_pytest, cwd)

    # Small helpers to extract information from pytest output
    @staticmethod
    def _extract_failing_test_nodeid(output: str) -> Optional[str]:
        # Look for file::test patterns
        m = re.search(r'([\w\./\\\-]+\.py::[^\s:,]+)', output)
        if m:
            return m.group(1)
        # Try summary form 'FAILED path/to/test_file.py::test_func - ...'
        m2 = re.search(r'FAILED\s+([^\s:]+\.py::[^\s\n]+)', output)
        if m2:
            return m2.group(1)
        return None

    @staticmethod
    def _extract_application_file_from_traceback(output: str, prefer_not_test: bool = True) -> Optional[str]:
        # Scan traceback 'File "..."' entries and pick a candidate
        candidates = []
        for m in re.finditer(r'File "([^"]+\.py)", line \d+, in', output):
            candidates.append(m.group(1))
        if not candidates:
            return None
        # Prefer non-test files from the deepest frames
        for p in reversed(candidates):
            try:
                if not os.path.exists(p):
                    continue
                bn = os.path.basename(p)
                if prefer_not_test and bn.startswith('test_'):
                    continue
                # exclude obvious system/venv paths heuristically
                low = p.lower()
                if any(x in low for x in ('site-packages', 'dist-packages', os.sep + 'lib' + os.sep + 'python', '/usr/lib')):
                    continue
                return os.path.normpath(p)
            except Exception:
                continue
        # fallback to last existing candidate
        for p in reversed(candidates):
            try:
                if os.path.exists(p):
                    return os.path.normpath(p)
                rel = os.path.join(os.getcwd(), p)
                if os.path.exists(rel):
                    return os.path.normpath(rel)
            except Exception:
                continue
        return None

    @staticmethod
    def _extract_error_summary(output: str) -> str:
        # Find 'E   ' lines
        for ln in output.splitlines():
            if ln.strip().startswith('E'):
                return ln.strip()
        # fallback to last non-empty line
        for ln in reversed(output.splitlines()):
            if ln.strip():
                return ln.strip()
        return ''

    async def run(self, goal, num_branches=3, iterations_per_branch=3):
        print(f"\nStarting workspace-aware improvement with goal: {goal}")
        # Deadlock prevention: check failure log before starting a new improvement
        try:
            if should_halt_for_goal(goal, threshold=2):
                print("\n[Improver] Aborting improvement: one or more tests associated with this goal have failed on the previous two consecutive improvement attempts.")
                print("Please ask a human developer to inspect the failing test(s) and the recent changes before attempting further automated improvements.")
                try:
                    fails = get_failures_for_goal(goal)
                    if fails:
                        print("\nFailing tests and consecutive failure counts:")
                        for tp, cnt in fails.items():
                            print(f" - {tp}: {cnt}")
                except Exception:
                    pass
                return
        except Exception:
            pass

        file_tree = self._scan_project_files()
        if not file_tree:
            print("No files found in project directory.")
            return

        # Use PlanningAndScaffoldingTask to produce the scaffolding plan
        planning_task = PlanningAndScaffoldingTask(goal)

        # Validation and self-correction loop
        max_retries = 2
        attempt = 0
        error_context: Optional[str] = None
        plan: Optional[ScaffoldingPlan] = None

        def _path_variants(p: str) -> Set[str]:
            variants = set()
            variants.add(p)
            variants.add(os.path.normpath(p))
            if p.startswith('./'):
                variants.add(p[2:]); variants.add(os.path.normpath(p[2:]))
            else:
                variants.add('./' + p); variants.add(os.path.normpath('./' + p))
            variants.add(p.lstrip('./'))
            variants.add(os.path.normpath(p.lstrip('./')))
            return variants

        while True:
            try:
                plan = await planning_task.execute(file_tree=file_tree, error_context=error_context)
            except TypeError:
                plan = await planning_task.execute(file_tree=file_tree)

            if not plan:
                print("PlanningAndScaffoldingTask returned no plan.")
                return

            if getattr(plan, 'reasoning', None):
                print(f"\nLLM Reasoning from scaffolding plan:\n{plan.reasoning}\n")

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
                break

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

        combined_files = set(plan.existing_files_to_edit) | set(plan.new_files_to_create)
        filtered_files = [f for f in combined_files if f not in self._protected_files]

        # Expand context
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

        runners = [BranchRunner(goal, self.safe_io, list(self._protected_files), i+1, iterations=iterations_per_branch).run(expanded_context_sorted) for i in range(num_branches)]
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
            original_files = [fp for fp in plan.existing_files_to_edit if fp not in self._protected_files]
            original = {fp: self.safe_io.read(fp) for fp in original_files}
        except Exception as e:
            print(f"Failed to read original files before applying changes: {e}")
            return

        if not any(original.get(e.file_path) != e.code for e in integration.edits if e.file_path not in self._protected_files):
            print("\nResult: No changes detected after integration.")
            return

        # Run tests in a sandbox with proposed edits applied before touching the repo
        try:
            with tempfile.TemporaryDirectory(prefix='improver-test-') as td:
                repo_root = os.path.abspath('.')
                # Copy project into tempdir (best-effort), skipping dot dirs and protected files
                for root, dirs, files in os.walk('.'):  # top-down
                    rel_root = os.path.relpath(root, '.')
                    if rel_root == '.':
                        rel_root = ''
                    # Skip hidden directories
                    skip_dir = False
                    for part in rel_root.split(os.sep):
                        if part.startswith('.'):  # skip dot folders like .git
                            skip_dir = True
                            break
                    if skip_dir:
                        continue
                    dest_root = os.path.join(td, rel_root)
                    os.makedirs(dest_root, exist_ok=True)
                    for f in files:
                        if f.startswith('.'):  # skip dot files
                            continue
                        src_fp = os.path.join(root, f)
                        norm_src = os.path.normpath(src_fp)
                        # Skip protected files
                        if norm_src in self._protected_files or f in self._protected_files:
                            continue
                        try:
                            shutil.copy2(src_fp, os.path.join(dest_root, f))
                        except Exception:
                            continue

                # Apply integrated edits into tempdir
                for edit in integration.edits:
                    if edit.file_path in self._protected_files:
                        continue
                    dest_fp = os.path.join(td, edit.file_path)
                    ddir = os.path.dirname(dest_fp)
                    if ddir:
                        os.makedirs(ddir, exist_ok=True)
                    try:
                        with open(dest_fp, 'w', encoding='utf-8') as f:
                            f.write(edit.code)
                    except Exception:
                        pass

                # Run pytest in the tempdir
                rc_td, out_td, err_td = await self._invoke_pytest_in_dir(td)
                pytest_output = (out_td or '') + '\n' + (err_td or '')

                if rc_td == 0:
                    print("Proposed changes passed tests in a sandbox. Proceeding to apply to repository.")
                    # Apply edits to real repository
                    for edit in integration.edits:
                        if edit.file_path in self._protected_files:
                            continue
                        self.safe_io.write(edit.file_path, edit.code)

                    # Re-run full test suite to verify no regressions
                    rc_all_after, out_all_after, err_all_after = await self._invoke_pytest_in_dir('.')
                    if rc_all_after == 0:
                        print("[Improv] Full test suite passes after fix. Continuing with original goal.")
                        try:
                            clear_failure_for_test(goal, test_log_key)
                        except Exception:
                            pass
                        return True
                    else:
                        print("[Improv] Full test suite reports failures after fix. Will record a failure and continue.")
                        try:
                            cnt = increment_failure(goal, test_log_key)
                            print(f"[Improver] Recorded automated fix-failure for goal='{goal}', test='{test_log_key}'. New consecutive failure count: {cnt}")
                            if cnt >= 3:
                                quarantine_test(test_log_key)
                                print(f"[Improv] Quarantined test due to repeated fix failures: {test_log_key}")
                        except Exception:
                            pass
                        return False
                else:
                    print("Proposed changes caused test failures in sandboxed run. Analyzing failures before applying to repo...")

                    test_nodeid = self._extract_failing_test_nodeid(pytest_output)
                    app_file = self._extract_application_file_from_traceback(pytest_output)
                    last_err = self._extract_error_summary(pytest_output)

                    # Attempt to use automated analysis (existing TestFailureAnalysisTask) if available
                    try:
                        from .testing import TestFailureAnalysisTask
                    except Exception:
                        TestFailureAnalysisTask = None

                    analysis_result = None
                    possible_test_file = None
                    if TestFailureAnalysisTask is not None:
                        test_source = None
                        if test_nodeid:
                            possible_test_file = test_nodeid.split('::')[0]
                        if possible_test_file:
                            try:
                                test_source = self.safe_io.read(possible_test_file)
                            except Exception:
                                try:
                                    with open(possible_test_file, 'r', encoding='utf-8') as f:
                                        test_source = f.read()
                                except Exception:
                                    test_source = None
                        analysis_task = TestFailureAnalysisTask(goal="Analyze pytest failure and determine cause")
                        try:
                            analysis_result = analysis_task.execute(pytest_output=pytest_output, test_file_path=possible_test_file, test_source=test_source)  # type: ignore
                        except TypeError:
                            try:
                                analysis_result = analysis_task.execute(pytest_output, possible_test_file, test_source)  # type: ignore
                            except Exception:
                                analysis_result = None

                    verdict = None
                    try:
                        if analysis_result is None:
                            print("No automated test-failure analysis available; proceeding to apply changes (best-effort).")
                        else:
                            if hasattr(analysis_result, 'dict'):
                                a = analysis_result.dict()
                            elif isinstance(analysis_result, dict):
                                a = analysis_result
                            else:
                                a = {
                                    'verdict': getattr(analysis_result, 'verdict', None),
                                    'confidence': getattr(analysis_result, 'confidence', None),
                                    'explanation': getattr(analysis_result, 'explanation', None),
                                    'suggested_fix': getattr(analysis_result, 'suggested_fix', None),
                                }
                            verdict = (a.get('verdict') or '').lower()
                            print(f"Test failure analysis verdict: {verdict}")
                    except Exception:
                        verdict = None

                    if verdict == 'application_code_bug':
                        # Do not apply edits automatically; present suggested fix to user (as before)
                        print("\n[Improv] Analysis indicates application_code_bug; not applying edits automatically.")
                        return False
                    elif verdict == 'test_flaw':
                        # Autonomous test-flaw handling could be placed here as a fallback, but the primary loop handles test_flaw elsewhere.
                        print("\n[Improv] Analysis reports test_flaw; continuing with normal flow.")
                        return False
                    else:
                        print("Analysis did not conclude 'application_code_bug' or 'test_flaw'; proceeding to apply edits to repo.")

        except Exception as e:
            print(f"Warning: Failed to run sandboxed pytest analysis: {e}. Proceeding to apply edits to repository.")

        # Apply edits to the real repository
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
        except Exception as e:
            print(f"Unexpected error while writing changes: {e}")
            return

        print(f"--- Finished multi-file improvement for files: {sorted(filtered_files)} ---")

        # Schedule pytest in background to observe results; failures should not block
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                asyncio.create_task(self._invoke_pytest_in_dir(getattr(self.safe_io, 'root_dir', os.path.abspath('.'))))
            else:
                threading.Thread(target=lambda: asyncio.run(self._invoke_pytest_in_dir(getattr(self.safe_io, 'root_dir', os.path.abspath('.')))), daemon=True).start()
        except Exception as e:
            print(f"Warning: Failed to schedule pytest run: {e}")

        return

    async def _start_high_priority_fix_loop(self, original_goal: str, test_log_key: str, test_nodeid: Optional[str], app_file: Optional[str], possible_test_file: Optional[str], test_source: Optional[str], extra_context_text: str) -> bool:
        """Attempt up to 3 autonomous fixes for a failing test as a separate, high-priority loop.

        Returns True if a fix was applied and the full test suite passes; False otherwise.
        """
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"[Improv] High-priority test-fix attempt {attempt} for '{test_log_key}' (goal: {original_goal})")
            test_fix_goal = f"Fix the broken test in {test_log_key}"
            # Determine targets: prioritize failing test and app code
            targets: List[str] = []
            if test_log_key:
                targets.append(test_log_key)
            if app_file:
                if app_file not in targets:
                    targets.append(app_file)
            if possible_test_file and possible_test_file not in targets:
                targets.append(possible_test_file)
            # Unique and return
            targets = list(dict.fromkeys(targets))
            if not targets:
                print("[Improv] No target files available for test-fix loop.")
                return False

            # Run a focused branch to produce edits
            branch = BranchRunner(goal=test_fix_goal, safe_io=self.safe_io, protected_files=list(self._protected_files), branch_id=attempt, iterations=1, max_corrections=3)
            plan_and_code = await branch.run(targets, extra_context=extra_context_text if extra_context_text else None)
            if not plan_and_code or not plan_and_code.edits:
                print("[Improv] No edits produced by test-fix branch.")
                # count as a failure for this test path
                try:
                    cnt = increment_failure(original_goal, test_log_key)
                    if cnt >= max_attempts:
                        quarantine_test(test_log_key)
                        print(f"[Improv] Quarantined test '{test_log_key}' after {cnt} failed fix attempts.")
                        return False
                except Exception:
                    pass
                continue

            # Apply edits to repository (tests and app files)
            for e in plan_and_code.edits:
                fp = getattr(e, 'file_path', None) if not isinstance(e, dict) else e.get('file_path')
                if not fp:
                    continue
                if fp in self._protected_files:
                    continue
                code = getattr(e, 'code', None) if not isinstance(e, dict) else e.get('code', '')
                self.safe_io.write(fp, code or '')

            # Run pytest in a sandbox-like manner by executing in the repo root
            rc, out, err = await self._invoke_pytest_in_dir(os.path.abspath('.'))
            pytest_output = (out or '') + '\n' + (err or '')

            if rc == 0:
                # Success! Clear the failure log for this test and restore original goal context
                try:
                    clear_failure_for_test(original_goal, test_log_key)
                except Exception:
                    pass
                print(f"[Improv] Autonomous test fix successful on attempt {attempt} for '{test_log_key}'.")
                # Apply changes already; now indicate success
                return True
            else:
                # Schedule another attempt
                try:
                    cnt = increment_failure(original_goal, test_log_key)
                    print(f"[Improv] Test-fix attempt {attempt} failed for '{test_log_key}'. Consecutive failures: {cnt}")
                    if cnt >= max_attempts:
                        quarantine_test(test_log_key)
                        print(f"[Improv] Quarantined test '{test_log_key}' after {cnt} failed fix attempts.")
                        return False
                except Exception:
                    pass
                # Continue loop for another attempt
                continue

        return False


# The file ends here with the updated Improver class implementing the test_flaw flow.
