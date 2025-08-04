# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Update the agent's architecture to allow each branch to run for multiple iterations in series. Modify the `improver.py` `run` method to accept a new `iterations_per_branch` parameter. The `_run_branch` method should be updated to loop for this number of iterations, using the code output from the previous iteration as the input for the next, all while working towards the same initial goal.