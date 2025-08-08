import asyncio
import os
import yaml
from typing import List, Set, Optional

from safe_io import SafeIO

from .planning import PlanningAndScaffoldingTask, ScaffoldingPlan
from .branch import BranchRunner
from .integration import IntegrationRunner
from .models import PlanAndCode
from .ast_utils import get_local_dependencies


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
