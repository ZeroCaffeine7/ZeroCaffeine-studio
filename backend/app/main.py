"""Minimal FastAPI API for the dispatcher PoC with merge endpoint and new task utilities."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List

from backend.app.state import TaskStateError
from backend.services.dispatcher import Dispatcher
from backend.services.merge_service import merge_project
from backend.app import storage

app = FastAPI(title="ZeroCaffeine Studio PoC", version="0.2.0")

# Allow the frontend served from localhost:8080 to interact with API during demo
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProjectInput(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)

class TaskInput(BaseModel):
    project_id: int
    title: str
    description: str
    role_name: str

class WorkerInput(BaseModel):
    worker_id: str
    role_name: str
    capacity: int = Field(1, ge=1)

class DispatchInput(BaseModel):
    task_ids: List[int]

class ClaimInput(BaseModel):
    worker_id: str

class CompleteInput(BaseModel):
    worker_id: str

class FailInput(BaseModel):
    reason: str | None = None

class Project(BaseModel):
    id: int
    title: str
    description: str
    status: str = "new"

class Task(BaseModel):
    id: int
    project_id: int
    title: str
    description: str
    role_name: str
    status: str = "new"
    assigned_worker_id: str | None = None

class Result(BaseModel):
    id: int
    task_id: int
    worker_name: str
    result_text: str

projects_db = {}  # lightweight cache not used for persistence

# Use storage-backed DB for persistent models

from backend.app.db import create_tables
create_tables()

from backend.app.db import SessionLocal

dispatcher = Dispatcher({}, lease_seconds=900)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ZeroCaffeine Studio PoC"}

@app.post("/projects", response_model=Project)
def create_project(project: ProjectInput):
    db = storage.get_db()
    try:
        proj = storage.create_project(db, project.title, project.description)
        return Project(id=proj.id, title=proj.title, description=proj.description, status=proj.status)
    finally:
        db.close()

@app.post("/tasks", response_model=Task)
def create_task(task: TaskInput):
    db = storage.get_db()
    try:
        proj = db.query(storage.ProjectModel).filter_by(id=task.project_id).first()
        if not proj:
            raise HTTPException(404, "Project not found")
        t = storage.create_task(db, task.project_id, task.title, task.description, task.role_name)
        return Task(id=t.id, project_id=t.project_id, title=t.title, description=t.description, role_name=t.role_name, status=t.status)
    finally:
        db.close()

@app.get("/tasks/project/{project_id}", response_model=List[Task])
def list_tasks(project_id: int):
    db = storage.get_db()
    try:
        tasks = storage.list_tasks_for_project(db, project_id)
        return [Task(id=t.id, project_id=t.project_id, title=t.title, description=t.description, role_name=t.role_name, status=t.status) for t in tasks]
    finally:
        db.close()

@app.get("/task/{task_id}", response_model=Task)
def get_task(task_id: int):
    db = storage.get_db()
    try:
        t = storage.get_task(db, task_id)
        if not t:
            raise HTTPException(404, "Task not found")
        return Task(id=t.id, project_id=t.project_id, title=t.title, description=t.description, role_name=t.role_name, status=t.status)
    finally:
        db.close()

@app.post("/workers")
def register_worker(worker: WorkerInput):
    db = storage.get_db()
    try:
        w = storage.register_worker(db, worker.worker_id, worker.role_name, worker.capacity)
        dispatcher.workers[w.id] = dispatcher.register_worker(w.id, w.role_name, w.capacity)
        return {"id": w.id, "role_name": w.role_name, "capacity": w.capacity, "active_tasks": w.active_tasks}
    finally:
        db.close()

@app.post("/dispatch")
def dispatch_tasks(request: DispatchInput):
    db = storage.get_db()
    try:
        # Simple behavior: push task ids into Redis queues for their role
        for tid in request.task_ids:
            t = storage.get_task(db, tid)
            if not t:
                continue
            from backend.services import queue_service
            queue_service.push_task(str(t.id), t.role_name)
        return {"assigned": len(request.task_ids)}
    finally:
        db.close()

@app.post("/tasks/{task_id}/claim", response_model=Task)
def claim_task(task_id: int, request: ClaimInput):
    db = storage.get_db()
    try:
        t = storage.get_task(db, task_id)
        if not t:
            raise HTTPException(404, "Task not found")
        # naive claim: set assigned_worker_id and status->in_progress
        t.assigned_worker_id = request.worker_id
        storage.update_task_status(db, t, 'in_progress', actor=request.worker_id)
        # ensure dispatcher worker tracking exists
        dispatcher.workers.setdefault(request.worker_id, dispatcher.register_worker(request.worker_id, t.role_name, 1))
        dispatcher.workers[request.worker_id].active_tasks += 1
        return Task(id=t.id, project_id=t.project_id, title=t.title, description=t.description, role_name=t.role_name, status=t.status)
    finally:
        db.close()

@app.post("/tasks/{task_id}/complete", response_model=Task)
def complete_task(task_id: int, request: CompleteInput):
    db = storage.get_db()
    try:
        t = storage.get_task(db, task_id)
        if not t:
            raise HTTPException(404, "Task not found")
        storage.update_task_status(db, t, 'completed', actor=request.worker_id)
        # decrement worker active tasks if tracked
        if request.worker_id in dispatcher.workers:
            dispatcher.workers[request.worker_id].active_tasks = max(0, dispatcher.workers[request.worker_id].active_tasks - 1)
        return Task(id=t.id, project_id=t.project_id, title=t.title, description=t.description, role_name=t.role_name, status=t.status)
    finally:
        db.close()

@app.post("/tasks/{task_id}/fail")
def fail_task(task_id: int, payload: FailInput):
    db = storage.get_db()
    try:
        t = storage.get_task(db, task_id)
        if not t:
            raise HTTPException(404, "Task not found")
        storage.mark_task_failed(db, t, reason=payload.reason, actor='worker')
        return {"task_id": task_id, "status": "failed"}
    finally:
        db.close()

@app.post("/tasks/{task_id}/result", response_model=Result)
def submit_result(task_id: int, result_payload: dict):
    db = storage.get_db()
    try:
        t = storage.get_task(db, task_id)
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        result = storage.submit_result(db, task_id, result_payload.get("worker_name", "unknown-worker"), result_payload.get("result_text", ""))
        # mark task completed if assigned
        storage.update_task_status(db, t, 'completed', actor=result.worker_name)
        # if task had retries tracked in redis, reset
        from backend.services import queue_service
        queue_service.reset_retry(str(task_id))
        return Result(id=result.id, task_id=result.task_id, worker_name=result.worker_name, result_text=result.result_text)
    finally:
        db.close()

@app.get("/dispatcher/queue")
def dispatcher_queue():
    from backend.services import queue_service
    # expire leases omitted for simplicity in DB-backed PoC
    return queue_service.list_queues()

@app.post("/projects/{project_id}/merge")
def project_merge(project_id: int):
    db = storage.get_db()
    try:
        proj = db.query(storage.ProjectModel).filter_by(id=project_id).first()
        if not proj:
            raise HTTPException(404, "Project not found")
        merged, repairs = merge_project(str(project_id), {}, {})
        return {"merged": merged, "repairs_created": repairs}
    finally:
        db.close()
