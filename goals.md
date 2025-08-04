# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Fundamentally upgrade the Improver in improver/orchestrator.py to use an autonomous scaffolding workflow, completely replacing the old file selection logic.
The run method must now import PlanningAndScaffoldingTask and ScaffoldingPlan from improver/planning.py.
Remove all usage of the old FileSelectionTask.
Instead, call the new PlanningAndScaffoldingTask. The response will be a ScaffoldingPlan.
After receiving the plan, the orchestrator must programmatically create the empty files listed in plan.new_files_to_create using self.safe_io.write(file_path, "").
The combined list of existing_files_to_edit and new_files_to_create should be passed to the AST dependency scanner to build the final, complete context for the branches.
Log the LLM's reasoning from the scaffolding plan to the console for user visibility.