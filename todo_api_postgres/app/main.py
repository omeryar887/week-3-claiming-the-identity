"""
main.py

Same five task endpoints, same shapes, same status codes as the A1
in-memory version. The only new thing is which TaskRepository gets
constructed at startup — everything below that line is untouched.

REPOSITORY_BACKEND controls which storage engine is active:
  "postgres" (default) -> PostgresTaskRepository (real Postgres, via DATABASE_URL)
  "memory"             -> InMemoryTaskRepository (for quick local testing, no DB needed)

Run with:  uvicorn app.main:app --reload
Docs at:   http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response

from app.repository import TaskRepository
from app.schemas import Task, TaskCreate, TaskUpdate

load_dotenv()

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A CRUD API for managing a to-do list, backed by Postgres in Docker.",
)


def _build_repository() -> TaskRepository:
    backend = os.getenv("REPOSITORY_BACKEND", "postgres").lower()
    if backend == "memory":
        from app.memory_repository import InMemoryTaskRepository

        return InMemoryTaskRepository()
    if backend == "postgres":
        from app.postgres_repository import PostgresTaskRepository

        return PostgresTaskRepository()
    raise RuntimeError(f"Unknown REPOSITORY_BACKEND: {backend!r} (expected 'postgres' or 'memory')")


repository: TaskRepository = _build_repository()


@app.get("/", summary="API info", description="Returns basic information about this API.")
def read_root() -> dict:
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": {"tasks": "/tasks"},
    }


@app.get("/health", summary="Health check", description="Returns ok, plus a real Postgres check (SELECT 1).")
def health_check() -> dict:
    db_status = "ok"
    try:
        repository.list_all()
    except Exception:
        db_status = "unreachable"
    return {"status": "ok", "db": db_status}


@app.get("/tasks", response_model=list[Task], summary="List all tasks")
def list_tasks() -> list[Task]:
    return repository.list_all()


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get a single task",
    description="Returns one task by ID. Returns 404 if no task with that ID exists.",
)
def get_task(task_id: int) -> Task:
    task = repository.get_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    description="Creates a new task. done always starts false. 400 if title is missing/empty.",
)
def create_task(payload: TaskCreate) -> Task:
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required and cannot be empty")
    return repository.create(title)


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update a task",
    description="Updates title and/or done. At least one field required. 404 unknown id, 400 invalid input.",
)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one of 'title' or 'done' to update",
        )

    title = None
    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")

    updated = repository.update(task_id, title, payload.done)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Deletes a task by ID. 404 if it doesn't exist.",
)
def delete_task(task_id: int) -> Response:
    deleted = repository.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
