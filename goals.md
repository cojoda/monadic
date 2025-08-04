# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Upgrade the Improver in improver/orchestrator.py to create a wider context for the AI.
The run method should be modified. After the initial files are selected by the FileSelectionTask, it must import and use the get_local_dependencies function from improver/ast_utils.py. Loop through the initially selected files, find all their local dependencies, and add them to a master set of files. This full, expanded set of context files should then be passed to the BranchRunner instances. Add print statements to log the initial selection vs. the final expanded context for debugging.