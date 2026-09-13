"""
schemas.py

Request/response models. Identical to the A1 in-memory version — the
whole point of this assignment is that swapping storage engines doesn't
touch these.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    title: str = Field(default="", description="The task's title. Must not be empty.")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, description="New title, if changing it.")
    done: bool | None = Field(default=None, description="New done status, if changing it.")
