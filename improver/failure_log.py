import json
import os
import time
from typing import Dict, Optional

# Path to JSON file storing failure counts. Keep at repo root.
LOG_PATH = os.environ.get('IMPROVER_TEST_FAILURE_LOG', 'test_failure_log.json')

_DEFAULT_STRUCTURE = {"goals": {}}


def _read_log() -> Dict:
    """Read the JSON log from disk. Return a dict with at least the top-level shape.

    Best-effort: any failure returns a fresh default structure to avoid raising in orchestrator flows.
    """
    try:
        if not os.path.exists(LOG_PATH):
            return _DEFAULT_STRUCTURE.copy()
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
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
        tmp = LOG_PATH + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # Atomic replace where available
        try:
            os.replace(tmp, LOG_PATH)
        except Exception:
            # Fallback to non-atomic write
            with open(LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
    except Exception:
        # Best-effort only; do not raise to avoid breaking orchestrator flows
        pass


def get_failures_for_goal(goal: str) -> Dict[str, int]:
    """Return a mapping of test_path -> consecutive failure count for the given goal."""
    data = _read_log()
    g = data.get('goals', {}).get(goal, {})
    out = {}
    for tp, info in (g or {}).items():
        try:
            out[tp] = int(info.get('count', 0))
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
    # Each entry is a dict containing at least 'count' and optionally 'last_failed'
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
    # If goal now empty, remove it
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
