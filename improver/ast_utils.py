import ast
import os
import sys
from typing import Set


def get_local_dependencies(file_path: str, project_root: str = '.') -> Set[str]:
    """
    Parse the given Python file and find local project dependencies from import statements.

    Args:
        file_path (str): Path to the Python source file to analyze.
        project_root (str): Root directory of the project for absolute import base.

    Returns:
        Set[str]: Set of normalized file paths of local dependencies.
    """
    # Only analyze Python source files. Ignore other file types.
    if not str(file_path).lower().endswith('.py'):
        return set()

    dependencies = set()
    project_root = os.path.abspath(project_root)
    file_path = os.path.abspath(file_path)
    file_dir = os.path.dirname(file_path)

    # Safely get standard library module names (available in Python 3.10+)
    stdlib_modules = getattr(sys, 'stdlib_module_names', set())

    # If file doesn't exist, nothing to do
    if not os.path.exists(file_path):
        return set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception:
        # If we can't read the file, treat as no dependencies.
        return set()

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        # If the Python file has syntax errors, we cannot reliably determine imports.
        return set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # For 'import module[.submodule]', check root module
            for alias in node.names:
                root_name = alias.name.split('.')[0]
                if root_name in stdlib_modules:
                    # Skip standard library modules
                    continue

                parts = alias.name.split('.')
                dep_path = os.path.join(project_root, *parts)

                if os.path.isdir(dep_path):
                    dep_path = os.path.join(dep_path, '__init__.py')
                else:
                    dep_path += '.py'

                try:
                    common = os.path.commonpath([project_root, os.path.abspath(dep_path)])
                    if common != project_root:
                        continue  # Not a local import
                except ValueError:
                    continue

                dep_path = os.path.normpath(dep_path)
                dependencies.add(dep_path)

        elif isinstance(node, ast.ImportFrom):
            module = node.module
            level = node.level  # number of leading dots

            root_name = module.split('.')[0] if module else None
            if root_name and root_name in stdlib_modules:
                # Skip standard library modules
                continue

            if level > 0:
                # Relative import: go up `level` directories from current file's directory
                base_dir = file_dir
                for _ in range(level):
                    base_dir = os.path.dirname(base_dir)

                if module:
                    parts = module.split('.')
                    dep_path = os.path.join(base_dir, *parts)
                    if os.path.isdir(dep_path):
                        dep_path = os.path.join(dep_path, '__init__.py')
                    else:
                        dep_path += '.py'
                else:
                    # e.g. from . import something (module is None)
                    dep_path = os.path.join(base_dir, '__init__.py')

                if not os.path.exists(dep_path):
                    continue

                try:
                    common = os.path.commonpath([project_root, os.path.abspath(dep_path)])
                    if common != project_root:
                        continue  # Not a local import
                except ValueError:
                    continue

                dependencies.add(os.path.normpath(dep_path))

            else:
                # Absolute import
                if module is None:
                    continue

                parts = module.split('.')

                # First attempt: resolve relative to project root
                dep_path_proj = os.path.join(project_root, *parts)
                if os.path.isdir(dep_path_proj):
                    candidate_path_proj = os.path.join(dep_path_proj, '__init__.py')
                else:
                    candidate_path_proj = dep_path_proj + '.py'

                if os.path.exists(candidate_path_proj):
                    try:
                        common = os.path.commonpath([project_root, os.path.abspath(candidate_path_proj)])
                        if common != project_root:
                            continue  # Not a local import
                    except ValueError:
                        continue
                    dependencies.add(os.path.normpath(candidate_path_proj))
                else:
                    # Fallback: resolve relative to current file directory
                    dep_path_file = os.path.join(file_dir, *parts)
                    if os.path.isdir(dep_path_file):
                        candidate_path_file = os.path.join(dep_path_file, '__init__.py')
                    else:
                        candidate_path_file = dep_path_file + '.py'

                    if os.path.exists(candidate_path_file):
                        try:
                            common = os.path.commonpath([project_root, os.path.abspath(candidate_path_file)])
                            if common != project_root:
                                continue  # Not a local import
                        except ValueError:
                            continue
                        dependencies.add(os.path.normpath(candidate_path_file))
                    else:
                        # Could not resolve the dependency path
                        continue

    return dependencies
