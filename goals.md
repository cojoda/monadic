# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement 'workspace awareness' by removing the `file_paths` parameter from the `Improver.run` method. The agent must now autonomously determine which files to edit by: 1. Scanning the project directory to create a file tree. 2. Using a new `FileSelectionTask` to ask the LLM to choose relevant files based on the goal and the file tree. 3. The prompt for this task must include the list of protected files as a strict constraint, forbidding the LLM from selecting them.