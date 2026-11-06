import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from app.config import settings

app = FastAPI(title=settings.app_name, version="1.0.0")

class TaskIn(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    done: bool = False

class Task(TaskIn):
    id: int

tasks: dict[int, Task] = {}   # in-memory; resets on new instance (fixed in P2)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env,
            "revision": os.getenv("K_REVISION", "local")}

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(body: TaskIn):
    new_id = max(tasks, default=0) + 1
    tasks[new_id] = Task(id=new_id, **body.model_dump())
    return tasks[new_id]

@app.get("/tasks", response_model=list[Task])
def list_tasks():
    return list(tasks.values())

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    return tasks[task_id]

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if tasks.pop(task_id, None) is None:
        raise HTTPException(404, "Task not found")
