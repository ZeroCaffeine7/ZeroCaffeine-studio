"""Task state machine used by the PoC API and dispatcher."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TaskState(Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MERGED = "merged"
    QA_PASSED = "qa_passed"
    QA_FAILED = "qa_failed"
    REVIEWED = "reviewed"
    FAILED = "failed"
    REWORK = "rework"


_ALLOWED_TRANSITIONS = {
    "new": {"assigned"},
    "assigned": {"in_progress", "failed"},
    "in_progress": {"completed", "failed", "rework"},
    "completed": {"merged"},
    "merged": {"qa_passed", "qa_failed"},
    "qa_failed": {"rework", "in_progress"},
    "qa_passed": {"reviewed"},
    "rework": {"in_progress", "failed"},
    "reviewed": set(),
    "failed": set(),
}

class TaskStateError(Exception):
    pass

_transition_history: Dict[str, List[Tuple[str, str, str, str]]] = {}


def _get(task, name, default=None):
    return getattr(task, name, task.get(name, default) if isinstance(task, dict) else default)


def _set(task, name, value):
    if isinstance(task, dict):
        task[name] = value
    else:
        setattr(task, name, value)


def can_transition(from_state: str, to_state: str) -> bool:
    return to_state in _ALLOWED_TRANSITIONS.get(from_state, set())


def record_transition(task_id: str, from_state: str, to_state: str, actor: Optional[str] = None) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    _transition_history.setdefault(task_id, []).append((timestamp, from_state, to_state, actor or "system"))


def get_task_state(tasks_db, task_id: str) -> Optional[str]:
    task = tasks_db.get(task_id)
    return _get(task, "status") if task else None


def get_task_history(task_id: str) -> List[Tuple[str, str, str, str]]:
    return list(_transition_history.get(task_id, []))


def transition_task_state(tasks_db, task_id: str, new_state: str, actor: Optional[str] = None):
    task = tasks_db.get(task_id)
    if task is None:
        raise TaskStateError(f"Task not found: {task_id}")
    current = _get(task, "status", TaskState.NEW.value)
    if current != new_state and not can_transition(current, new_state):
        raise TaskStateError(f"Invalid transition from '{current}' to '{new_state}' for task {task_id}")
    _set(task, "status", new_state)
    record_transition(task_id, current, new_state, actor)
    return task


def assign_task(tasks_db, task_id, actor=None):
    return transition_task_state(tasks_db, task_id, "assigned", actor)


def start_task(tasks_db, task_id, actor=None):
    return transition_task_state(tasks_db, task_id, "in_progress", actor)


def complete_task(tasks_db, task_id, actor=None):
    return transition_task_state(tasks_db, task_id, "completed", actor)
