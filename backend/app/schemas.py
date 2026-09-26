from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class TaskCreate(BaseModel):
    project_id: str
    title: str
    description: str
    role_name: str


class ResultCreate(BaseModel):
    worker_name: str
    result_text: str


class ReviewCreate(BaseModel):
    reviewer_name: str = "Manager"
    status: str = "pending"
    comments: str = ""
