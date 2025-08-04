# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Update the system prompts in improver/branch.py and improver/integration.py to empower the agents with full multi-file refactoring and creation capabilities.
1. In improver/branch.py, modify the BranchTask system prompt. It should no longer be told just to "rewrite given files." Change it to state that it can use the files as context to achieve a goal, and that its output can include edits for existing files or for completely new files it invents.
2. In improver/integration.py, modify the IntegratorTask prompt. It must be told that it will be reviewing proposals that may have different file structures and may include newly created files, and that its job is to choose the best architectural approach.