"""
memory_repository.py

The original A1 storage, now expressed against the TaskRepository
interface. Kept in the repo (not deleted) specifically so the "swap"
this assignment is about is visible as a diff between this file and
postgres_repository.py — same interface, different engine underneath.

Not used by default (see app/config.py) — Postgres is the active
backend for this assignment's submission.
"""

from __future__ import annotations

from app.repository import TaskRepository
from app.schemas import Task


class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._tasks: list[Task] = [
            Task(id=1, title="Buy groceries", done=False),
            Task(id=2, title="Read a book", done=False),
            Task(id=3, title="Write project report", done=True),
        ]
        self._next_id = 4

    def list_all(self) -> list[Task]:
        return list(self._tasks)

    def get_by_id(self, task_id: int) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def create(self, title: str) -> Task:
        task = Task(id=self._next_id, title=title, done=False)
        self._tasks.append(task)
        self._next_id += 1
        return task

    def update(self, task_id: int, title: str | None, done: bool | None) -> Task | None:
        task = self.get_by_id(task_id)
        if task is None:
            return None
        updated = task.model_copy(
            update={
                "title": title if title is not None else task.title,
                "done": done if done is not None else task.done,
            }
        )
        self._tasks[self._tasks.index(task)] = updated
        return updated

    def delete(self, task_id: int) -> bool:
        task = self.get_by_id(task_id)
        if task is None:
            return False
        self._tasks.remove(task)
        return True
