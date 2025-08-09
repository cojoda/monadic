import json
import os
import time
from typing import Dict, Optional

# Path to JSON file storing failure counts. Keep at repo root.
LOG_PATH = os.environ.get('IMPROVER_TEST_FAILURE_LOG', 'test_failure_log.json')
# Path to quarantine list for tests that failed repeatedly
QUARANTINE_PATH = os.environ.get('IMPROVER_QUARANTINE_PATH', 'quarantined_tests.json')

_DEFAULT_STRUCTURE = {"goals": {}}


def _ensure_parent_dir(path: str) -> None:
    try:
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
    except Exception:
        # Best-effort only
        pass


def _read_log() -> Dict:
    """Read the JSON log from disk. Return a dict with at least the top-level shape.

    Best-effort: any failure returns a fresh default structure to avoid raising in orchestrator flows.
    If the file does not exist, attempt to create it with the default structure (best-effort).
    """
    try:
        if not os.path.exists(LOG_PATH):
            # try to create the file on disk to reduce races later
            try:
                _ensure_parent_dir(LOG_PATH)
                _write_log(_DEFAULT_STRUCTURE.copy())
            except Exception:
                pass
            return _DEFAULT_STRUCTURE.copy()

        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                # Corrupt file: return default structure
                return _DEFAULT_STRUCTURE.copy()

            if not isinstance(data, dict):
                return _DEFAULT_STRUCTURE.copy()
            if 'goals' not in data or not isinstance(data['goals'], dict):
                data = {'goals': {}}
            return data
    except Exception:
        return _DEFAULT_STRUCTURE.copy()


def _write_log(data: Dict) -> None:
    """Write the JSON log atomically if possible. Best-effort: swallow errors to avoid breaking flows."""
    try:
        _ensure_parent_dir(LOG_PATH)
        tmp = LOG_PATH + '.tmp'
        # write to temp file first
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.flush()
        # atomic replace where available
        try:
            os.replace(tmp, LOG_PATH)
        except Exception:
            # fallback to non-atomic write
            with open(LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
    except Exception:
        # Best-effort only; do not raise to avoid breaking orchestrator flows
        pass


def get_failures_for_goal(goal: str) -> Dict[str, int]:
    """Return a mapping of test_path -> consecutive failure count for the given goal."""
    data = _read_log()
    g = data.get('goals', {}).get(goal, {})
    out: Dict[str, int] = {}
    for tp, info in (g or {}).items():
        try:
            # support legacy shapes where value might be an int
            if isinstance(info, dict):
                out[tp] = int(info.get('count', 0))
            else:
                out[tp] = int(info)
        except Exception:
            out[tp] = 0
    return out


def should_halt_for_goal(goal: str, threshold: int = 2) -> bool:
    """Return True if any test for goal has failed at least `threshold` times consecutively."""
    fails = get_failures_for_goal(goal)
    for cnt in fails.values():
        try:
            if cnt >= int(threshold):
                return True
        except Exception:
            continue
    return False


def increment_failure(goal: str, test_path: str) -> int:
    """Increment consecutive failure count for (goal, test_path). Returns new count."""
    data = _read_log()
    goals = data.setdefault('goals', {})
    g = goals.setdefault(goal, {})
    entry = g.setdefault(test_path, {})
    try:
        cnt = int(entry.get('count', 0)) + 1
    except Exception:
        cnt = 1
    entry['count'] = cnt
    entry['last_failed'] = int(time.time())
    _write_log(data)
    return cnt


def clear_failure_for_test(goal: str, test_path: str) -> None:
    """Clear recorded failure for a specific test under a goal."""
    data = _read_log()
    if 'goals' not in data:
        return
    g = data['goals'].get(goal)
    if not g:
        return
    if test_path in g:
        try:
            del g[test_path]
        except Exception:
            pass
    # if goal now empty, remove it
    if not g:
        try:
            del data['goals'][goal]
        except Exception:
            pass
    _write_log(data)


def clear_goal(goal: str) -> None:
    """Clear all recorded failures for a goal."""
    data = _read_log()
    if 'goals' not in data:
        return
    if goal in data['goals']:
        try:
            del data['goals'][goal]
            _write_log(data)
        except Exception:
            pass


def get_all() -> Dict:
    """Return the entire log structure (best-effort)."""
    return _read_log()


# Quarantine helpers (new)

def _read_quarantine() -> list:
    if not os.path.exists(QUARANTINE_PATH):
        return []
    try:
        with open(QUARANTINE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get('quarantined', []), list):
                return data['quarantined']
    except Exception:
        pass
    return []


def _write_quarantine(lst: list) -> None:
    try:
        _ensure_parent_dir(QUARANTINE_PATH)
        with open(QUARANTINE_PATH, 'w', encoding='utf-8') as f:
            json.dump({"quarantined": lst}, f, indent=2)
    except Exception:
        pass


def quarantine_test(test_path: str) -> None:
    """Add a test_path to quarantine list and persist to disk."""
    try:
        lst = _read_quarantine()
        if test_path not in lst:
            lst.append(test_path)
            _write_quarantine(lst)
            print(f"[Improv] Quarantined test: {test_path}")
    except Exception:
        pass


def is_quarantined(test_path: str) -> bool:
    try:
        return test_path in _read_quarantine()
    except Exception:
        return False
