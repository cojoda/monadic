import asyncio
import os
import yaml
from typing import List, Set

from safe_io import SafeIO

from .selection import FileSelectionTask
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

        selected_resp = await FileSelectionTask(goal).execute(file_tree=file_tree, protected_files=sorted(self._protected_files))
        selected_files = [f for f in (getattr(selected_resp, 'selected_files', []) or []) if f not in self._protected_files]
        if not selected_files:
            print("No files to improve after filtering protected files.")
            return

        # Expand context by including local dependencies
        expanded_context: Set[str] = set(selected_files)
        for file_path in selected_files:
            try:
                deps = get_local_dependencies(file_path)
                expanded_context.update(deps)
            except Exception as e:
                print(f"Warning: Failed to get local dependencies for {file_path}: {e}")

        expanded_context_sorted = sorted(expanded_context)

        print(f"Initially selected files for improvement (excluding protected): {selected_files}")
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
            original = {fp: self.safe_io.read(fp) for fp in selected_files}
        except Exception as e:
            print(f"Failed to read original files before applying changes: {e}")
            return

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
        print(f"--- Finished multi-file improvement for files: {selected_files} ---")
