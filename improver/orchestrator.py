# improver/orchestrator.py
import asyncio
import os
import yaml
import subprocess
import sys
from typing import List, Optional, Tuple, Any

# --- Start of CRITICAL FIX ---
# Ensure the name 'SafeIO' is always defined before the class is parsed.
# This prevents the NameError during class definition.
SafeIO = None

# Now, attempt the robust import.
try:
    from safe_io import SafeIO
except (ModuleNotFoundError, ImportError):
    try:
        from ..safe_io import SafeIO
    except (ImportError, ValueError):
        # This fallback is for when the module is truly not findable.
        # The program will fail later with a clearer error if SafeIO is actually used.
        pass
# --- End of CRITICAL FIX ---

from .planning import PlanningAndScaffoldingTask
from .branch import BranchRunner
from .integration import IntegrationRunner
from .ast_utils import get_local_dependencies


class Improver:
    """The main orchestrator that runs the end-to-end improvement process."""

    # Use a string forward reference for the type hint ('SafeIO').
    # This avoids the NameError by deferring the type hint's evaluation.
    def __init__(self, safe_io: "SafeIO", default_num_branches: int = 3, default_iterations_per_branch: int = 3):
        if safe_io is None:
            raise ImportError("Could not import the SafeIO class. Please ensure safe_io.py is in the correct path.")
        self.safe_io = safe_io
        self._default_num_branches = int(default_num_branches)
        self._default_iterations_per_branch = int(default_iterations_per_branch)
        self._protected_files = set()
        try:
            # The path to protected.yaml is now correctly handled by the sandboxed SafeIO
            content = self.safe_io.read('protected.yaml')
            if content:
                loaded = yaml.safe_load(content)
                if isinstance(loaded, list):
                    self._protected_files = set(loaded)
        except Exception:
            pass

    def _scan_project_files(self) -> List[str]:
        """
        Scans the project directory specified by safe_io.project_root
        and returns a list of relative file paths.
        """
        project_root = self.safe_io.project_root
        files = []
        for root, dirs, fnames in os.walk(project_root):
            # Exclude directories starting with a dot
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in fnames:
                if f.startswith('.'):
                    continue
                full_path = os.path.join(root, f)
                relative_path = os.path.relpath(full_path, project_root)
                files.append(relative_path)
        files.sort()
        return files

    async def run(self, goal: str, num_branches: Optional[int] = None, iterations_per_branch: Optional[int] = None):
        print(f"\nStarting improvement for goal: {goal}")
        print(f"Targeting project directory: {self.safe_io.project_root}")

        file_tree = self._scan_project_files()
        if not file_tree:
            print("No files found in the target project directory.")
            return

        planning_task = PlanningAndScaffoldingTask(goal)
        plan = await planning_task.execute(file_tree=file_tree)

        if not plan:
            print("Planning failed. Could not generate an improvement plan.")
            return

        if getattr(plan, 'reasoning', None):
            print(f"\nLLM Reasoning:\n{plan.reasoning}\n")

        # Create new files first, as per the plan
        for new_file in getattr(plan, 'new_files_to_create', []):
            self.safe_io.write(new_file, "") # Create with empty content

        combined_files = set(getattr(plan, 'existing_files_to_edit', [])) | set(getattr(plan, 'new_files_to_create', []))
        
        # Determine effective branching and iteration counts
        nb = num_branches if num_branches is not None else self._default_num_branches
        iters = iterations_per_branch if iterations_per_branch is not None else self._default_iterations_per_branch
        
        # Run branches
        branch_runners = [
            BranchRunner(goal, self.safe_io, list(self._protected_files), i + 1, iterations=iters).run(list(combined_files))
            for i in range(nb)
        ]
        results = await asyncio.gather(*branch_runners)

        proposals = [
            {"id": i + 1, "plan": r.reasoning, "edits": r.edits}
            for i, r in enumerate(results) if r and r.edits
        ]

        if not proposals:
            print("\nNo successful improvement proposals were generated.")
            return

        # Integrate proposals
        integration_runner = IntegrationRunner(goal, self.safe_io)
        final_plan = await integration_runner.run(proposals)

        if not final_plan or not final_plan.edits:
            print("\nIntegration failed or produced no changes.")
            return

        # Apply the final, integrated changes
        print("\nApplying integrated changes...")
        for edit in final_plan.edits:
            if edit.file_path in self._protected_files:
                print(f"Skipping write to protected file: {edit.file_path}")
                continue
            self.safe_io.write(edit.file_path, edit.code)

        print(f"--- Improvement run for goal '{goal}' completed successfully. ---")