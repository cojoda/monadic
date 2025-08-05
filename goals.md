# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement a validation and self-correction loop for the planning phase.

In improver/orchestrator.py, after the initial ScaffoldingPlan is generated, add a validation and self-correction loop to ensure the plan is viable before proceeding.

The new logic should:

Iterate through the existing_files_to_edit list from the generated plan.

For each file, use os.path.exists() to verify it is present on the filesystem.

If any file does not exist, the plan is considered invalid. The system should then:
a.  Construct a detailed error message explaining which file was not found.
b.  Re-run the PlanningAndScaffoldingTask, providing the error message as new context to correct the plan.
c.  This retry loop should be attempted a maximum of 2 times before failing.

To support this, improver/planning.py must also be modified:

The construct_prompt method in PlanningAndScaffoldingTask needs to be updated to accept an optional error context string, which will be added to the prompt to guide the AI's correction.