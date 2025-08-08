import ast
import os
import sys
import importlib.util
import sysconfig
from typing import Set
from pathlib import Path


def _normalize_path(p: str) -> str:
    try:
        # Use realpath to resolve symlinks, then normalize
        return os.path.normpath(os.path.realpath(os.path.abspath(p)))
    except Exception:
        return p


def _is_in_project(path: str, project_root: str) -> bool:
    try:
        abs_path = _normalize_path(path)
        proj_root = _normalize_path(project_root)
        common = os.path.commonpath([proj_root, abs_path])
        return common == proj_root
    except Exception:
        return False


def _get_stdlib_paths():
    """Return a set of filesystem paths that are considered part of the stdlib.

    This uses sysconfig to determine the stdlib and platstdlib locations and
    normalizes them for prefix checking.
    """
    paths = set()
    try:
        cfg = sysconfig.get_paths()
        for key in ("stdlib", "platstdlib"):
            p = cfg.get(key)
            if p:
                paths.add(_normalize_path(p))
    except Exception:
        pass

    # Also include sys.base_prefix/lib... fallback for some environments
    try:
        base = getattr(sys, "base_prefix", None) or getattr(sys, "prefix", None)
        if base:
            pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
            candidate = os.path.join(base, "lib", pyver)
            paths.add(_normalize_path(candidate))
    except Exception:
        pass

    # Normalize and remove empty entries
    return {p for p in paths if p}


_STD_PATHS = _get_stdlib_paths()


def _is_stdlib_module(module_name: str) -> bool:
    """Return True if module_name is part of the Python standard library.

    The function accepts dotted names and will check the root name first using
    fast builtin lists if available. If not conclusively identified, it will
    attempt to find a spec and inspect the origin or package locations to see
    whether the implementation lives inside one of the stdlib directories or is
    a builtin/frozen module.
    """
    if not module_name:
        return False

    root = module_name.split(".")[0]

    # Check fast builtin lists if available
    try:
        std_names = set(getattr(sys, "stdlib_module_names", set()))
    except Exception:
        std_names = set()
    try:
        std_names |= set(getattr(sys, "builtin_module_names", ()))
    except Exception:
        pass

    if root in std_names:
        return True

    # Try to inspect spec origin
    try:
        spec = importlib.util.find_spec(root)
    except Exception:
        spec = None

    if not spec:
        return False

    origin = getattr(spec, "origin", None)
    locations = getattr(spec, "submodule_search_locations", None)

    # Builtin/frozen modules: treat as stdlib
    if origin in (None, "built-in", "frozen") and not locations:
        return True

    # If origin is a filesystem path: check if it's under any stdlib path
    if isinstance(origin, str):
        origin_norm = _normalize_path(origin)
        for sp in _STD_PATHS:
            if origin_norm == sp or origin_norm.startswith(sp + os.sep):
                return True

    # For namespace/package locations, check each location
    if locations:
        for loc in locations:
            try:
                loc_norm = _normalize_path(loc)
                for sp in _STD_PATHS:
                    if loc_norm == sp or loc_norm.startswith(sp + os.sep):
                        return True
            except Exception:
                continue

    return False


def _spec_points_to_project(spec, project_root: str) -> str:
    """
    Given a ModuleSpec, determine if it points to a file/location inside project_root.
    If so, return a normalized path to the module file (or __init__.py for packages). Otherwise return an empty string.
    """
    if not spec:
        return ''

    origin = getattr(spec, 'origin', None)
    locations = getattr(spec, 'submodule_search_locations', None)

    # Builtin/frozen modules
    if origin in (None, 'built-in', 'frozen') and not locations:
        # builtin/frozen -> not a project file
        return ''

    proj_root = _normalize_path(project_root)

    # If there are submodule_search_locations (package directories), check them
    if locations:
        for loc in locations:
            try:
                if _is_in_project(loc, proj_root):
                    init_py = os.path.join(loc, '__init__.py')
                    if os.path.exists(init_py):
                        return _normalize_path(init_py)
                    return _normalize_path(loc)
            except Exception:
                continue
        return ''

    # Otherwise, origin should be a file path
    if origin and isinstance(origin, str):
        origin_norm = _normalize_path(origin)

        # If the origin is a compiled file inside __pycache__ or a .pyc, try to map to .py
        if origin_norm.endswith('.pyc') or '__pycache__' in origin_norm.split(os.sep):
            # Attempt simple mapping to .py
            try:
                # remove __pycache__ components
                parts = origin_norm.split(os.sep)
                if '__pycache__' in parts:
                    idx = parts.index('__pycache__')
                    # drop the __pycache__ piece
                    parts.pop(idx)
                    # last part might be modulename.cpython-38.pyc -> try to strip suffix after first dot
                    last = parts[-1]
                    if '.py' in last:
                        # map to .py (best-effort)
                        base = last.split('.py')[0]
                        parts[-1] = base + '.py'
                    origin_norm = _normalize_path(os.sep.join(parts))
                else:
                    # .pyc -> .py (best-effort)
                    origin_norm = origin_norm[:-1]
            except Exception:
                pass

        if _is_in_project(origin_norm, proj_root):
            # If it's a file in the project, return it
            return origin_norm
    return ''


def get_local_dependencies(file_path: str, project_root: str = '.') -> Set[str]:
    """
    Parse the given Python file and find local project dependencies from import statements.

    This function only attempts to parse files that clearly have a .py extension
    (case-insensitive). Non-Python files are ignored and result in an empty set.

    Args:
        file_path (str): Path to the Python source file to analyze.
        project_root (str): Root directory of the project for absolute import base.

    Returns:
        Set[str]: Set of normalized file paths of local dependencies.
    """
    # Be robust to Path-like inputs and ensure we only handle .py files
    try:
        p = Path(file_path)
    except Exception:
        return set()

    if p.suffix.lower() != '.py':
        return set()

    dependencies = set()
    project_root = _normalize_path(project_root)
    file_path = _normalize_path(str(p))
    file_dir = os.path.dirname(file_path)

    # If file doesn't exist or is not a regular file, nothing to do
    if not os.path.isfile(file_path):
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
            for alias in node.names:
                full_name = alias.name
                root_name = full_name.split('.')[0]

                # Ignore stdlib modules right away
                if _is_stdlib_module(root_name):
                    continue

                # Try to use importlib to see where this module would come from
                spec = None
                try:
                    spec = importlib.util.find_spec(full_name)
                except Exception:
                    spec = None

                # If spec points into the project, use that path
                spec_path = _spec_points_to_project(spec, project_root)
                if spec_path:
                    dependencies.add(spec_path)
                    continue

                # If spec exists but points outside project (installed package or stdlib), ignore
                if spec is not None:
                    continue

                # Fallback: attempt to resolve inside project layout
                parts = full_name.split('.')
                dep_path = os.path.join(project_root, *parts)

                if os.path.isdir(dep_path):
                    dep_path = os.path.join(dep_path, '__init__.py')
                else:
                    dep_path += '.py'

                if not os.path.exists(dep_path):
                    # Not present inside project
                    continue

                if not _is_in_project(dep_path, project_root):
                    continue

                dependencies.add(_normalize_path(dep_path))

        elif isinstance(node, ast.ImportFrom):
            module = node.module
            level = node.level  # number of leading dots

            root_name = module.split('.')[0] if module else None
            if root_name and _is_stdlib_module(root_name):
                continue

            if level > 0:
                # Relative import: go up `level` directories from current file's directory
                base_dir = file_dir
                # level==1 means current package (the package containing file), so don't go up
                for _ in range(max(0, level - 1)):
                    base_dir = os.path.dirname(base_dir)

                if module:
                    parts = module.split('.')
                    dep_path = os.path.join(base_dir, *parts)
                    if os.path.isdir(dep_path):
                        dep_path = os.path.join(dep_path, '__init__.py')
                    else:
                        dep_path += '.py'
                else:
                    # e.g. from . import something -> check package's __init__.py or adjacent module
                    dep_path = os.path.join(base_dir, '__init__.py')

                if not os.path.exists(dep_path):
                    continue

                if not _is_in_project(dep_path, project_root):
                    continue

                dependencies.add(_normalize_path(dep_path))

            else:
                # Absolute import
                if module is None:
                    continue

                # If the root module is stdlib, skip
                if _is_stdlib_module(module.split('.')[0]):
                    continue

                # Try importlib first
                spec = None
                try:
                    spec = importlib.util.find_spec(module)
                except Exception:
                    spec = None

                spec_path = _spec_points_to_project(spec, project_root)
                if spec_path:
                    dependencies.add(spec_path)
                    continue

                if spec is not None:
                    # module exists but outside project (external package or stdlib)
                    continue

                parts = module.split('.')

                # First attempt: resolve relative to project root
                dep_path_proj = os.path.join(project_root, *parts)
                if os.path.isdir(dep_path_proj):
                    candidate_path_proj = os.path.join(dep_path_proj, '__init__.py')
                else:
                    candidate_path_proj = dep_path_proj + '.py'

                if os.path.exists(candidate_path_proj) and _is_in_project(candidate_path_proj, project_root):
                    dependencies.add(_normalize_path(candidate_path_proj))
                    continue

                # Fallback: resolve relative to current file directory
                dep_path_file = os.path.join(file_dir, *parts)
                if os.path.isdir(dep_path_file):
                    candidate_path_file = os.path.join(dep_path_file, '__init__.py')
                else:
                    candidate_path_file = dep_path_file + '.py'

                if os.path.exists(candidate_path_file) and _is_in_project(candidate_path_file, project_root):
                    dependencies.add(_normalize_path(candidate_path_file))
                    continue

                # Could not resolve dependency path or it's external
                continue

    return dependencies
