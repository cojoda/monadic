import ast
import os
import sys
import importlib.util
import sysconfig
import site
from typing import Set
from pathlib import Path


def _normalize_path(p: str) -> str:
    try:
        # Resolve symlinks and normalize
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

    Uses sysconfig and sensible fallbacks.
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

    # Also include a common base/lib/pythonX.Y fallback
    try:
        base = getattr(sys, "base_prefix", None) or getattr(sys, "prefix", None)
        if base:
            pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
            candidate = os.path.join(base, "lib", pyver)
            paths.add(_normalize_path(candidate))
    except Exception:
        pass

    # Try to include the directory containing some builtin module file (best-effort)
    try:
        import os as _os_mod
        of = getattr(_os_mod, '__file__', None)
        if of:
            paths.add(_normalize_path(os.path.dirname(of)))
    except Exception:
        pass

    return {p for p in paths if p}


def _get_site_paths():
    """Return a set of filesystem paths that are considered installed package locations (site-packages).

    Includes global site-packages, user site-packages, and heuristics from sys.path.
    """
    paths = set()
    try:
        if hasattr(site, "getsitepackages"):
            for p in site.getsitepackages():
                if p:
                    paths.add(_normalize_path(p))
    except Exception:
        pass

    try:
        usersite = site.getusersitepackages()
        if usersite:
            paths.add(_normalize_path(usersite))
    except Exception:
        pass

    try:
        for p in sys.path:
            if not p:
                continue
            lp = p.lower()
            if 'site-packages' in lp or 'dist-packages' in lp:
                paths.add(_normalize_path(p))
    except Exception:
        pass

    # Prefix-based guesses
    try:
        base = getattr(sys, "base_prefix", None) or getattr(sys, "prefix", None)
        if base:
            pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
            candidate = os.path.join(base, "lib", "python", pyver, "site-packages")
            paths.add(_normalize_path(candidate))
            candidate2 = os.path.join(base, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
            paths.add(_normalize_path(candidate2))
    except Exception:
        pass

    return {p for p in paths if p}


_STD_PATHS = _get_stdlib_paths()
_SITE_PATHS = _get_site_paths()


def _is_stdlib_path(path: str) -> bool:
    """Return True if the given filesystem path is located inside any known stdlib path."""
    try:
        if not path:
            return False
        p = _normalize_path(path)
        for sp in _STD_PATHS:
            if p == sp or p.startswith(sp + os.sep):
                return True
    except Exception:
        pass
    return False


def _is_stdlib_module(module_name: str) -> bool:
    """Return True if module_name is part of the Python standard library.

    Accepts dotted names; checks fast builtin lists when available and falls back
    to inspecting importlib.ModuleSpec origin/locations.
    """
    if not module_name:
        return False

    root = module_name.split(".")[0]

    # Fast checks
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

    # Inspect spec origin/locations
    try:
        spec = importlib.util.find_spec(root)
    except Exception:
        spec = None

    if not spec:
        return False

    origin = getattr(spec, "origin", None)
    locations = getattr(spec, "submodule_search_locations", None)

    # builtin/frozen
    if origin in (None, "built-in", "frozen") and not locations:
        return True

    if isinstance(origin, str):
        origin_norm = _normalize_path(origin)
        if _is_stdlib_path(origin_norm):
            return True

    if locations:
        for loc in locations:
            try:
                if _is_stdlib_path(_normalize_path(loc)):
                    return True
            except Exception:
                continue

    return False


def _spec_points_to_project(spec, project_root: str) -> str:
    """
    Given a ModuleSpec, determine if it points to a file/location inside project_root.
    If so, return a normalized path to the module file (or __init__.py for packages).
    Otherwise return an empty string.
    """
    if not spec:
        return ''

    origin = getattr(spec, 'origin', None)
    locations = getattr(spec, 'submodule_search_locations', None)

    # builtin/frozen
    if origin in (None, 'built-in', 'frozen') and not locations:
        return ''

    proj_root = _normalize_path(project_root)

    # If origin points into stdlib or site-packages, treat as not in-project
    try:
        if isinstance(origin, str):
            origin_norm = _normalize_path(origin)
            for sp in _STD_PATHS:
                if origin_norm == sp or origin_norm.startswith(sp + os.sep):
                    return ''
            for sp in _SITE_PATHS:
                if origin_norm == sp or origin_norm.startswith(sp + os.sep):
                    return ''
    except Exception:
        pass

    # If package directories are present, check them
    if locations:
        for loc in locations:
            try:
                loc_norm = _normalize_path(loc)
                # Skip stdlib or site-packages
                skip = False
                for sp in _STD_PATHS:
                    if loc_norm == sp or loc_norm.startswith(sp + os.sep):
                        skip = True
                        break
                if skip:
                    continue
                for sp in _SITE_PATHS:
                    if loc_norm == sp or loc_norm.startswith(sp + os.sep):
                        skip = True
                        break
                if skip:
                    continue

                if _is_in_project(loc_norm, proj_root):
                    init_py = os.path.join(loc_norm, '__init__.py')
                    if os.path.exists(init_py):
                        return _normalize_path(init_py)
                    return _normalize_path(loc_norm)
            except Exception:
                continue
        return ''

    # Otherwise origin should be a file path
    if origin and isinstance(origin, str):
        origin_norm = _normalize_path(origin)

        # Map .pyc / __pycache__ to .py where possible
        if origin_norm.endswith('.pyc') or '__pycache__' in origin_norm.split(os.sep):
            try:
                parts = origin_norm.split(os.sep)
                if '__pycache__' in parts:
                    idx = parts.index('__pycache__')
                    parts.pop(idx)
                    last = parts[-1]
                    if '.py' in last:
                        base = last.split('.py')[0]
                        parts[-1] = base + '.py'
                    origin_norm = _normalize_path(os.sep.join(parts))
                else:
                    # .pyc -> .py (best-effort)
                    if origin_norm.endswith('.pyc'):
                        origin_norm = origin_norm[:-1]
            except Exception:
                pass

        # Exclude stdlib or site-packages
        try:
            for sp in _STD_PATHS:
                if origin_norm == sp or origin_norm.startswith(sp + os.sep):
                    return ''
            for sp in _SITE_PATHS:
                if origin_norm == sp or origin_norm.startswith(sp + os.sep):
                    return ''
        except Exception:
            pass

        if _is_in_project(origin_norm, proj_root):
            return origin_norm
    return ''


def _is_valid_project_path(candidate: str, project_root: str) -> bool:
    """Return True if candidate exists, is inside project_root, and is not in stdlib/site-packages."""
    try:
        if not candidate:
            return False
        candidate_norm = _normalize_path(candidate)
        if not os.path.exists(candidate_norm):
            return False
        if not _is_in_project(candidate_norm, project_root):
            return False
        if _is_stdlib_path(candidate_norm):
            return False
        # Also ensure it's not inside site-packages locations
        for sp in _SITE_PATHS:
            try:
                if candidate_norm == sp or candidate_norm.startswith(sp + os.sep):
                    return False
            except Exception:
                continue
        return True
    except Exception:
        return False


def get_local_dependencies(file_path: str, project_root: str = '.') -> Set[str]:
    """
    Parse the given Python file and find local project dependencies from import statements.

    Only .py files are analyzed. Returns normalized file paths for dependencies
    that are inside project_root and are not standard-library or installed packages.
    """
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

    if not os.path.isfile(file_path):
        return set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception:
        return set()

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                full_name = alias.name
                root_name = full_name.split('.')[0]

                # Ignore stdlib modules quickly
                if _is_stdlib_module(root_name) or _is_stdlib_module(full_name):
                    continue

                # Ask importlib where it would come from
                spec = None
                try:
                    spec = importlib.util.find_spec(full_name)
                except Exception:
                    spec = None

                # If spec points into the project, accept it
                spec_path = _spec_points_to_project(spec, project_root)
                if spec_path and _is_valid_project_path(spec_path, project_root):
                    dependencies.add(spec_path)
                    continue

                # If spec exists but not in project, treat as external and skip
                if spec is not None:
                    continue

                # Fallback: attempt to resolve inside project layout
                parts = full_name.split('.')
                dep_path = os.path.join(project_root, *parts)

                if os.path.isdir(dep_path):
                    dep_candidate = os.path.join(dep_path, '__init__.py')
                else:
                    dep_candidate = dep_path + '.py'

                if _is_valid_project_path(dep_candidate, project_root):
                    dependencies.add(_normalize_path(dep_candidate))

        elif isinstance(node, ast.ImportFrom):
            module = node.module
            level = node.level

            # Determine root name for stdlib check
            root_name = module.split('.')[0] if module else None
            if root_name and _is_stdlib_module(root_name):
                continue

            if level > 0:
                # Relative import: ascend from file_dir
                base_dir = file_dir
                for _ in range(max(0, level - 1)):
                    base_dir = os.path.dirname(base_dir)

                if module:
                    parts = module.split('.')
                    dep_path = os.path.join(base_dir, *parts)
                    if os.path.isdir(dep_path):
                        dep_candidate = os.path.join(dep_path, '__init__.py')
                    else:
                        dep_candidate = dep_path + '.py'
                else:
                    dep_candidate = os.path.join(base_dir, '__init__.py')

                if _is_valid_project_path(dep_candidate, project_root):
                    dependencies.add(_normalize_path(dep_candidate))

            else:
                # Absolute import
                if module is None:
                    continue

                if _is_stdlib_module(module.split('.')[0]) or _is_stdlib_module(module):
                    continue

                spec = None
                try:
                    spec = importlib.util.find_spec(module)
                except Exception:
                    spec = None

                spec_path = _spec_points_to_project(spec, project_root)
                if spec_path and _is_valid_project_path(spec_path, project_root):
                    dependencies.add(spec_path)
                    continue

                if spec is not None:
                    # Module is present but outside project -> external
                    continue

                parts = module.split('.')

                # Resolve relative to project root first
                dep_path_proj = os.path.join(project_root, *parts)
                if os.path.isdir(dep_path_proj):
                    candidate_path_proj = os.path.join(dep_path_proj, '__init__.py')
                else:
                    candidate_path_proj = dep_path_proj + '.py'

                if _is_valid_project_path(candidate_path_proj, project_root):
                    dependencies.add(_normalize_path(candidate_path_proj))
                    continue

                # Fallback relative to current file directory
                dep_path_file = os.path.join(file_dir, *parts)
                if os.path.isdir(dep_path_file):
                    candidate_path_file = os.path.join(dep_path_file, '__init__.py')
                else:
                    candidate_path_file = dep_path_file + '.py'

                if _is_valid_project_path(candidate_path_file, project_root):
                    dependencies.add(_normalize_path(candidate_path_file))
                    continue

    return dependencies
