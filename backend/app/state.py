"""
Task state machine for ZeroCaffeine Studio PoC

Provides a simple, explicit task lifecycle and helper functions to validate
and perform state transitions. Keeps an in-memory history of transitions for
the PoC; production should persist this to the database (audit_logs table).

Usage (example):

from backend.app.state import transition_task_state, get_task_state, get_task_history

# tasks_db is the in-memory dict in backend/app/main.py
transition_task_state(tasks_db, "task-1", "assigned", actor="WorldDesigner")

"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime


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


# Allowed transitions map
_ALLOWED_TRANSITIONS: Dict[TaskState, List[TaskState]] = {
    TaskState.NEW: [TaskState.ASSIGNED],
    TaskState.ASSIGNED: [TaskState.IN_PROGRESS, TaskState.FAILED],
    TaskState.IN_PROGRESS: [TaskState.COMPLETED, TaskState.FAILED, TaskState.REWORK],
    TaskState.COMPLETED: [TaskState.MERGED],
    TaskState.MERGED: [TaskState.QA_PASSED, TaskState.QA_FAILED],
    TaskState.QA_FAILED: [TaskState.REWORK, TaskState.IN_PROGRESS],
    TaskState.QA_PASSED: [TaskState.REVIEWED],
    TaskState.REWORK: [TaskState.IN_PROGRESS, TaskState.FAILED],
    TaskState.REVIEWED: [],
    TaskState.FAILED: [],
}


class TaskStateError(Exception):
    pass


# In-memory transition history for PoC. Production systems MUST persist this.
_transition_history: Dict[str, List[Tuple[str, str, str]]] = {}


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def get_task_state(tasks_db: Dict[str, dict], task_id: str) -> Optional[str]:
    """Return the current state string for a task_id or None if task not found."""
    task = tasks_db.get(task_id)
    if not task:
        return None
    return task.get("status")


def can_transition(from_state: str, to_state: str) -> bool:
    """Check whether transition from->to is allowed.

    Both from_state and to_state are strings representing TaskState values.
    """
    try:
        f = TaskState(from_state)
        t = TaskState(to_state)
    except ValueError:
        return False
    allowed = _ALLOWED_TRANSITIONS.get(f, [])
    return t in allowed


def record_transition(task_id: str, from_state: str, to_state: str, actor: Optional[str] = None) -> None:
    """Record a transition entry in the in-memory history.

    Each entry is (timestamp_iso, from_state, to_state, actor)
    """
    entry = (_now_iso(), from_state, to_state, actor or "system")
    _transition_history.setdefault(task_id, []).append(entry)


def get_task_history(task_id: str) -> List[Tuple[str, str, str]]:
    """Return recorded transition history for a task_id."""
    return _transition_history.get(task_id, [])


def transition_task_state(tasks_db: Dict[str, dict], task_id: str, new_state: str, actor: Optional[str] = None) -> dict:
    """Attempt to transition the task to new_state.

    - Validates that the task exists
    - Validates allowed transitions
    - Updates tasks_db[task_id]['status'] on success
    - Records transition history

    Returns the updated task dict.

    Raises TaskStateError on invalid transitions or missing task.
    """
    if task_id not in tasks_db:
        raise TaskStateError(f"Task not found: {task_id}")

    task = tasks_db[task_id]
    current = task.get("status") or TaskState.NEW.value

    if current == new_state:
        # No-op but record it
        record_transition(task_id, current, new_state, actor)
        return task

    if not can_transition(current, new_state):
        raise TaskStateError(f"Invalid transition from '{current}' to '{new_state}' for task {task_id}")

    # Perform the transition
    task["status"] = new_state
    record_transition(task_id, current, new_state, actor)

    return task


# Convenience helpers
def assign_task(tasks_db: Dict[str, dict], task_id: str, actor: Optional[str] = None) -> dict:
    return transition_task_state(tasks_db, task_id, TaskState.ASSIGNED.value, actor=actor)


def start_task(tasks_db: Dict[str, dict], task_id: str, actor: Optional[str] = None) -> dict:
    return transition_task_state(tasks_db, task_id, TaskState.IN_PROGRESS.value, actor=actor)


def complete_task(tasks_db: Dict[str, dict], task_id: str, actor: Optional[str] = None) -> dict:
    return transition_task_state(tasks_db, task_id, TaskState.COMPLETED.value, actor=actor)


def merge_task(tasks_db: Dict[str, dict], task_id: str, actor: Optional[str] = None) -> dict:
    return transition_task_state(tasks_db, task_id, TaskState.MERGED.value, actor=actor)


def mark_qa_passed(tasks_db: Dict[str, dict], task_id: str, actor: Optional[str] = None) -> dict:
    return transition_task_state(tasks_db, task_id, TaskState.QA_PASSED.value, actor=actor)


def mark_qa_failed(tasks_db: Dict[str, dict], task_id: str, actor: Optional[str] = None) -> dict:
    return transition_task_state(tasks_db, task_id, TaskState.QA_FAILED.value, actor=actor)
