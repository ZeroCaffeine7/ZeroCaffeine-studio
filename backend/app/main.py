from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="ZeroCaffeine Studio PoC", version="0.1.0")


class ProjectInput(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class TaskInput(BaseModel):
    project_id: str
    title: str
    description: str
    role_name: str


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


class Result(BaseModel):
    id: str
    task_id: str
    worker_name: str
    result_text: str


class Review(BaseModel):
    id: str
    project_id: str
    reviewer_name: str = "Manager"
    status: str = "pending"
    comments: str = ""


projects_db: dict[str, Project] = {}
tasks_db: dict[str, Task] = {}
results_db: dict[str, Result] = {}
reviews_db: dict[str, Review] = {}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ZeroCaffeine Studio PoC"}


@app.post("/projects", response_model=Project)
def create_project(project: ProjectInput):
    project_id = f"proj-{len(projects_db) + 1}"
    created = Project(
        id=project_id,
        title=project.title,
        description=project.description,
        status="new",
    )
    projects_db[project_id] = created
    return created


@app.get("/projects", response_model=List[Project])
def list_projects():
    return list(projects_db.values())


@app.post("/tasks", response_model=Task)
def create_task(task: TaskInput):
    if task.project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    task_id = f"task-{len(tasks_db) + 1}"
    created = Task(
        id=task_id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        role_name=task.role_name,
        status="new",
    )
    tasks_db[task_id] = created
    return created


@app.get("/tasks/{project_id}", response_model=List[Task])
def list_tasks_for_project(project_id: str):
    return [task for task in tasks_db.values() if task.project_id == project_id]


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
    tasks_db[task_id].status = "completed"
    return result


@app.get("/tasks/{task_id}/results", response_model=List[Result])
def list_results(task_id: str):
    return [result for result in results_db.values() if result.task_id == task_id]


@app.post("/projects/{project_id}/review", response_model=Review)
def create_review(project_id: str, review_payload: dict):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    review = Review(
        id=f"rev-{len(reviews_db) + 1}",
        project_id=project_id,
        reviewer_name=review_payload.get("reviewer_name", "Manager"),
        status=review_payload.get("status", "pending"),
        comments=review_payload.get("comments", ""),
    )
    reviews_db[review.id] = review
    return review
