# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- The dependency scanner in improver/ast_utils.py is incorrectly identifying standard library modules (like functools and typing) as local project files, causing errors. This goal is to fix that by making the scanner "standard library aware."

In improver/ast_utils.py, modify the get_local_dependencies function:

It must get a list of all standard library module names. The best way to do this is using the sys.stdlib_module_names set, which is available in Python 3.10 and later. Ensure you import sys.
Inside the loop that processes ast.Import and ast.ImportFrom nodes, check if the root of the imported module's name (e.g., the "functools" in "functools.cached_property") is in the set of standard library names.
If the module is a standard library module, you must continue to the next node and NOT attempt to resolve it as a local file path. The function should only return paths to files that are actually part of the local project.