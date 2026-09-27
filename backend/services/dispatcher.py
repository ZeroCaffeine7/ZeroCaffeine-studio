"""In-memory dispatcher for the Level Design PoC.

The dispatcher is deliberately storage-agnostic: it receives the same task
store used by the API and maintains only assignment/lease metadata. Replace
this with Redis/Kafka/Temporal-backed storage when scaling beyond the PoC.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from backend.app.state import TaskStateError, assign_task, start_task


@dataclass
class Worker:
    worker_id: str
    role_name: str
    capacity: int = 1
    active_tasks: int = 0

    @property
    def available(self) -> bool:
        return self.active_tasks < self.capacity


@dataclass
class Lease:
    task_id: str
    worker_id: str
    expires_at: datetime


class Dispatcher:
    """Role-aware, capacity-limited task dispatcher for the PoC."""

    def __init__(self, tasks_db: dict, lease_seconds: int = 900):
        self.tasks_db = tasks_db
        self.lease_seconds = lease_seconds
        self.workers: Dict[str, Worker] = {}
        self.leases: Dict[str, Lease] = {}

    def register_worker(self, worker_id: str, role_name: str, capacity: int = 1) -> Worker:
        worker = Worker(worker_id, role_name, max(1, capacity))
        self.workers[worker_id] = worker
        return worker

    def register_pool(self, role_name: str, count: int, capacity: int = 1) -> List[Worker]:
        return [
            self.register_worker(f"{role_name}-worker-{i + 1}", role_name, capacity)
            for i in range(count)
        ]

    def _value(self, task, name: str, default=None):
        return getattr(task, name, task.get(name, default) if isinstance(task, dict) else default)

    def _set(self, task, name: str, value) -> None:
        if isinstance(task, dict):
            task[name] = value
        else:
            setattr(task, name, value)

    def expire_leases(self) -> int:
        now = datetime.now(timezone.utc)
        expired = [task_id for task_id, lease in self.leases.items() if lease.expires_at <= now]
        for task_id in expired:
            lease = self.leases.pop(task_id)
            worker = self.workers.get(lease.worker_id)
            if worker:
                worker.active_tasks = max(0, worker.active_tasks - 1)
            task = self.tasks_db.get(task_id)
            if task and self._value(task, "status") == "assigned":
                self._set(task, "status", "new")
        return len(expired)

    def _candidate_workers(self, role_name: str) -> Iterable[Worker]:
        return sorted(
            (w for w in self.workers.values() if w.role_name == role_name and w.available),
            key=lambda w: (w.active_tasks, w.worker_id),
        )

    def dispatch(self, task_ids: List[str], actor: str = "dispatcher") -> List[dict]:
        """Assign as many queued tasks as capacity allows."""
        self.expire_leases()
        assignments = []
        for task_id in task_ids:
            task = self.tasks_db.get(task_id)
            if not task or self._value(task, "status") != "new":
                continue
            role_name = self._value(task, "role_name")
            worker = next(iter(self._candidate_workers(role_name)), None)
            if worker is None:
                continue
            assign_task(self.tasks_db, task_id, actor=actor)
            worker.active_tasks += 1
            lease = Lease(
                task_id,
                worker.worker_id,
                datetime.now(timezone.utc) + timedelta(seconds=self.lease_seconds),
            )
            self.leases[task_id] = lease
            self._set(task, "assigned_worker_id", worker.worker_id)
            assignments.append({"task_id": task_id, "worker_id": worker.worker_id, "role_name": role_name})
        return assignments

    def claim(self, task_id: str, worker_id: str) -> dict:
        task = self.tasks_db.get(task_id)
        worker = self.workers.get(worker_id)
        if not task or not worker:
            raise TaskStateError("Task or worker not found")
        if self._value(task, "role_name") != worker.role_name:
            raise TaskStateError("Worker role does not match task role")
        if self._value(task, "status") != "assigned":
            raise TaskStateError("Only assigned tasks can be claimed")
        assigned = self._value(task, "assigned_worker_id")
        if assigned and assigned != worker_id:
            raise TaskStateError("Task is assigned to another worker")
        start_task(self.tasks_db, task_id, actor=worker_id)
        return task

    def complete(self, task_id: str, worker_id: str) -> dict:
        task = self.tasks_db.get(task_id)
        if not task or self._value(task, "assigned_worker_id") != worker_id:
            raise TaskStateError("Worker does not own this task")
        if self._value(task, "status") != "in_progress":
            raise TaskStateError("Only in-progress tasks can be completed")
        self._set(task, "status", "completed")
        lease = self.leases.pop(task_id, None)
        if lease and lease.worker_id in self.workers:
            self.workers[lease.worker_id].active_tasks = max(0, self.workers[lease.worker_id].active_tasks - 1)
        return task

    def queue_snapshot(self) -> dict:
        counts = {}
        for task in self.tasks_db.values():
            status = self._value(task, "status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return {"tasks_by_status": counts, "workers": [w.__dict__ for w in self.workers.values()]}
