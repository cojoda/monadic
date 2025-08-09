# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- In improver/orchestrator.py, modify the Improver.run method. It should now create an instance of WorkflowContext at the beginning of the run. Update the call to the PlanningAndScaffoldingTask to use the goal and file_tree from this new context object.