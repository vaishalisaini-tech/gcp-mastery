import os, time, logging
from fastapi import FastAPI, HTTPException, status, Depends, Request, Header
from app.config import settings
from app.logging_config import setup_logging

setup_logging()
log = logging.getLogger("task-tracker")

app = FastAPI(title=settings.app_name, version="1.1.0")


def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    log.info("request", extra={"extra_fields": {
        "method": request.method, "path": request.url.path,
        "status": response.status_code,
        "latency_ms": round((time.perf_counter() - start) * 1000, 1)}})
    return response

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

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_api_key)])
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

@app.delete("/tasks/{task_id}", status_code=204, dependencies=[Depends(require_api_key)])
def delete_task(task_id: int):
    if tasks.pop(task_id, None) is None:
        raise HTTPException(404, "Task not found")

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=100)
    done: bool | None = None

@app.patch("/tasks/{task_id}", response_model=Task, dependencies=[Depends(require_api_key)])
def update_task(task_id: int, body: TaskUpdate):
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")

    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(400, "No fields provided to update")

    tasks[task_id] = tasks[task_id].model_copy(update=changes)
    return tasks[task_id]

