"""Minimal FastAPI API for the dispatcher PoC."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

from backend.app.state import TaskStateError
from backend.services.dispatcher import Dispatcher

app = FastAPI(title="ZeroCaffeine Studio PoC", version="0.2.0")

class ProjectInput(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)

class TaskInput(BaseModel):
    project_id: str
    title: str
    description: str
    role_name: str

class WorkerInput(BaseModel):
    worker_id: str
    role_name: str
    capacity: int = Field(1, ge=1)

class DispatchInput(BaseModel):
    task_ids: List[str]

class ClaimInput(BaseModel):
    worker_id: str

class CompleteInput(BaseModel):
    worker_id: str

class Project(BaseModel):
    id: str
    title: str
    description: str
    status: str = "new"

class Task(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    role_name: str
    status: str = "new"
    assigned_worker_id: str | None = None

projects_db: dict[str, Project] = {}
tasks_db: dict[str, Task] = {}
dispatcher = Dispatcher(tasks_db)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ZeroCaffeine Studio PoC"}

@app.post("/projects", response_model=Project)
def create_project(project: ProjectInput):
    project_id = f"proj-{len(projects_db) + 1}"
    created = Project(id=project_id, title=project.title, description=project.description)
    projects_db[project_id] = created
    return created

@app.post("/tasks", response_model=Task)
def create_task(task: TaskInput):
    if task.project_id not in projects_db:
        raise HTTPException(404, "Project not found")
    task_id = f"task-{len(tasks_db) + 1}"
    created = Task(id=task_id, project_id=task.project_id, title=task.title,
                   description=task.description, role_name=task.role_name)
    tasks_db[task_id] = created
    return created

@app.get("/tasks/{project_id}", response_model=List[Task])
def list_tasks(project_id: str):
    return [task for task in tasks_db.values() if task.project_id == project_id]

@app.post("/workers")
def register_worker(worker: WorkerInput):
    return dispatcher.register_worker(worker.worker_id, worker.role_name, worker.capacity).__dict__

@app.post("/dispatch")
def dispatch_tasks(request: DispatchInput):
    try:
        return {"assignments": dispatcher.dispatch(request.task_ids)}
    except TaskStateError as error:
        raise HTTPException(409, str(error))

@app.post("/tasks/{task_id}/claim", response_model=Task)
def claim_task(task_id: str, request: ClaimInput):
    try:
        return dispatcher.claim(task_id, request.worker_id)
    except TaskStateError as error:
        raise HTTPException(409, str(error))

@app.post("/tasks/{task_id}/complete", response_model=Task)
def complete_task(task_id: str, request: CompleteInput):
    try:
        return dispatcher.complete(task_id, request.worker_id)
    except TaskStateError as error:
        raise HTTPException(409, str(error))

@app.get("/dispatcher/queue")
def dispatcher_queue():
    dispatcher.expire_leases()
    return dispatcher.queue_snapshot()
