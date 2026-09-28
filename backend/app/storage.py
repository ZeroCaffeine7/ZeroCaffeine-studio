"""Simple storage helpers wrapping SQLAlchemy for PoC API.

This module provides convenience CRUD functions used by the API. It's minimal
and intentionally synchronous for simplicity; production systems should use
connection pooling and async frameworks as needed.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app import db as _db
from backend.app.models import Project as ProjectModel, Task as TaskModel, Result as ResultModel, Worker as WorkerModel, Transition as TransitionModel


def get_db():
    return _db.SessionLocal()


# Projects
def create_project(db: Session, title: str, description: str) -> ProjectModel:
    proj = ProjectModel(title=title, description=description)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


def list_projects(db: Session) -> List[ProjectModel]:
    return db.query(ProjectModel).order_by(ProjectModel.created_at.desc()).all()


# Tasks
def create_task(db: Session, project_id: int, title: str, description: str, role_name: str) -> TaskModel:
    task = TaskModel(project_id=project_id, title=title, description=description, role_name=role_name)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks_for_project(db: Session, project_id: int) -> List[TaskModel]:
    return db.query(TaskModel).filter(TaskModel.project_id==project_id).order_by(TaskModel.id).all()


def get_task(db: Session, task_id: int) -> Optional[TaskModel]:
    return db.query(TaskModel).filter(TaskModel.id==task_id).first()


def update_task_status(db: Session, task: TaskModel, status: str, actor: Optional[str]=None) -> TaskModel:
    prev = task.status
    task.status = status
    db.add(task)
    # record transition (use previous state as from_state)
    tr = TransitionModel(task_id=task.id, from_state=prev, to_state=status, actor=actor or 'system')
    db.add(tr)
    db.commit()
    db.refresh(task)
    return task


def mark_task_failed(db: Session, task: TaskModel, reason: Optional[str]=None, actor: Optional[str]=None) -> TaskModel:
    prev = task.status
    task.status = 'failed'
    db.add(task)
    tr = TransitionModel(task_id=task.id, from_state=prev, to_state='failed', actor=actor or 'system')
    db.add(tr)
    db.commit()
    db.refresh(task)
    return task


# Results
def submit_result(db: Session, task_id: int, worker_name: str, result_text: str) -> ResultModel:
    result = ResultModel(task_id=task_id, worker_name=worker_name, result_text=result_text)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def list_results_for_task(db: Session, task_id: int) -> List[ResultModel]:
    return db.query(ResultModel).filter(ResultModel.task_id==task_id).all()


# Workers
def register_worker(db: Session, worker_id: str, role_name: str, capacity: int=1) -> WorkerModel:
    worker = db.query(WorkerModel).filter(WorkerModel.id==worker_id).first()
    if worker is None:
        worker = WorkerModel(id=worker_id, role_name=role_name, capacity=capacity, active_tasks=0)
        db.add(worker)
    else:
        worker.role_name = role_name
        worker.capacity = capacity
    db.commit()
    db.refresh(worker)
    return worker


def list_workers(db: Session) -> List[WorkerModel]:
    return db.query(WorkerModel).all()
