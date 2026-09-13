"""
postgres_repository.py

Implements TaskRepository against a real Postgres database. Every query
here uses a parameterized placeholder (%s, psycopg's style) — the task
id or title is always passed as a separate argument, never glued into
the SQL string. This is what keeps user input from being able to alter
the query.

The table is created automatically if it doesn't exist, and the three
example tasks are seeded only if the table is empty — same first-run
rule as the in-memory version's starting data.
"""

from __future__ import annotations

from app.db import get_pool
from app.repository import TaskRepository
from app.schemas import Task

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);
"""

_SEED_TASKS = [
    ("Buy groceries", False),
    ("Read a book", False),
    ("Write project report", True),
]


class PostgresTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLE_SQL)
                cur.execute("SELECT COUNT(*) FROM tasks;")
                (count,) = cur.fetchone()
                if count == 0:
                    for title, done in _SEED_TASKS:
                        cur.execute(
                            "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                            (title, done),
                        )
            conn.commit()

    def list_all(self) -> list[Task]:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, done FROM tasks ORDER BY id;")
                rows = cur.fetchall()
        return [Task(id=r[0], title=r[1], done=r[2]) for r in rows]

    def get_by_id(self, task_id: int) -> Task | None:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
                row = cur.fetchone()
        if row is None:
            return None
        return Task(id=row[0], title=row[1], done=row[2])

    def create(self, title: str) -> Task:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
                    (title, False),
                )
                row = cur.fetchone()
            conn.commit()
        return Task(id=row[0], title=row[1], done=row[2])

    def update(self, task_id: int, title: str | None, done: bool | None) -> Task | None:
        existing = self.get_by_id(task_id)
        if existing is None:
            return None

        new_title = title if title is not None else existing.title
        new_done = done if done is not None else existing.done

        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done;",
                    (new_title, new_done, task_id),
                )
                row = cur.fetchone()
            conn.commit()
        return Task(id=row[0], title=row[1], done=row[2])

    def delete(self, task_id: int) -> bool:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
                deleted = cur.rowcount > 0
            conn.commit()
        return deleted
