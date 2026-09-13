"""
repository.py

The repository interface. Both the in-memory store (from A1/A2) and the
Postgres store implement exactly this shape. The service/route layer in
main.py only ever talks to this interface — it never imports a concrete
repository directly. That's what makes "swap the storage" a one-file
change instead of a rewrite.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import Task


class TaskRepository(ABC):
    """Contract every storage backend must satisfy."""

    @abstractmethod
    def list_all(self) -> list[Task]:
        ...

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task | None:
        ...

    @abstractmethod
    def create(self, title: str) -> Task:
        ...

    @abstractmethod
    def update(self, task_id: int, title: str | None, done: bool | None) -> Task | None:
        """Returns the updated Task, or None if task_id doesn't exist."""
        ...

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        """Returns True if a task was deleted, False if task_id didn't exist."""
        ...
