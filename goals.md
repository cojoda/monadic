# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement a new utility for static analysis in the empty file improver/ast_utils.py.
Create a function get_local_dependencies(file_path: str, project_root: str = '.') -> Set[str]. This function should use Python's ast module to parse the given Python file. It needs to walk the AST to find all ast.ImportFrom nodes and identify local project imports (both relative like from .models and absolute like from improver.core). It must return a set of normalized file paths for these discovered dependencies.