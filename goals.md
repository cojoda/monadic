# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- The dependency scanner in improver/ast_utils.py is failing to resolve absolute imports of project modules correctly, leading to "File not found" errors. It must be upgraded to check multiple locations.

In improver/ast_utils.py, modify the get_local_dependencies function. The logic for handling absolute imports (where the AST node's level is 0) must be changed.

Instead of only checking for the module path at the project root, it must implement a two-step check:

First, try to resolve the path relative to the project root, just as it does now. If the file exists, add it to the set of dependencies.
If and only if that fails, try to resolve the path relative to the directory of the file currently being parsed. If this second check finds a valid file, add that to the dependencies.
This dual-check will correctly resolve modules that are imported by their simple name from within the same package directory (e.g., from core import ... inside another file in the improver package).