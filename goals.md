# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Improve dependency analysis to differentiate between local modules and installed packages.

This will involve the following changes to `improver/ast_utils.py`:
1.  **Check Standard Library**: Before assuming a module is a local file, check if it's part of Python's standard library. If it is, ignore it.
2.  **Validate Local Paths**: When an import is not in the standard library, ensure that the file path it resolves to is actually within the project directory. This will prevent the agent from trying to find installed packages in the local file system.