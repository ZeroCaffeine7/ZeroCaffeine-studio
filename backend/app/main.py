"""Minimal FastAPI API for the dispatcher PoC with merge endpoint."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

from backend.app.state import TaskStateError
from backend.services.dispatcher import Dispatcher
from backend.services.merge_service import merge_project

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

class Result(BaseModel):
    id: str
    task_id: str
    worker_name: str
    result_text: str

projects_db: dict[str, Project] = {}
tasks_db: dict[str, Task] = {}
results_db: dict[str, Result] = {}
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

@app.post("/tasks/{task_id}/result", response_model=Result)
def submit_result(task_id: str, result_payload: dict):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    result = Result(
        id=f"res-{len(results_db) + 1}",
        task_id=task_id,
        worker_name=result_payload.get("worker_name", "unknown-worker"),
        result_text=result_payload.get("result_text", ""),
    )
    results_db[result.id] = result
    # mark task completed if assigned
    try:
        dispatcher.complete(task_id, result.worker_name)
    except Exception:
        # ignore lease ownership in PoC result submission
        tasks_db[task_id].status = "completed"
    return result

@app.post("/projects/{project_id}/merge")
def project_merge(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(404, "Project not found")
    merged, repairs = merge_project(project_id, tasks_db, results_db)
    return {"merged": merged, "repairs_created": repairs}
