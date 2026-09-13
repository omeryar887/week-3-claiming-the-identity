# Task API — Postgres in Docker

The same Task CRUD API, now backed by a real PostgreSQL database running
in Docker, started together with the app via a single `docker compose up`.

## What this is

Three storage engines, same API, same behaviour:
- **A1** — an in-memory Python list (gone on restart)
- **A2** — SQLite (a single file on disk)
- **A3 (this)** — Postgres, running as its own containerized server

The routes never changed across any of these swaps. What changed each
time is a single file: the repository. See `app/repository.py` for the
interface, `app/memory_repository.py` for the original in-memory
version (kept for comparison), and `app/postgres_repository.py` for
this assignment's real implementation. `app/main.py` — the routes —
is identical in shape to the A1 version.

## One command to run everything

```bash
git clone <your-repo-url>
cd todo_api_postgres
cp .env.example .env
docker compose up
```

That's it — `docker compose up` builds the app image, starts Postgres
in its own container, and connects them. On first run the app creates
the `tasks` table and seeds three example tasks.

Test it:
```bash
curl -i http://localhost:3000/tasks
```

Stop everything with `docker compose down` (data survives — see
"Persistence" below). To wipe the data too: `docker compose down -v`.

## Running without Docker Compose (Stages 0–3, step by step)

If you want to work through this the way the assignment stages it,
rather than jumping straight to compose:

```bash
# Stage 0 — Postgres in Docker, by itself
docker run --name taskdb -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=tasks \
  -p 5432:5432 -v taskdata:/var/lib/postgresql/data -d postgres

docker ps                                              # confirm it's running
docker exec -it taskdb psql -U postgres -d tasks       # open a SQL prompt
# \dt        -> no tables yet (the app creates it on first connect)
# \q         -> quit

# Stage 1 — connect the app
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # DATABASE_URL already points at localhost:5432

uvicorn app.main:app --reload  # creates the table + seeds 3 tasks on startup

# In another terminal, confirm the table exists and has 3 rows:
docker exec -it taskdb psql -U postgres -d tasks -c "\dt"
docker exec -it taskdb psql -U postgres -d tasks -c "SELECT * FROM tasks;"

# Stages 2–3 — read / create / update / delete
curl -i http://localhost:8000/tasks
curl -i http://localhost:8000/tasks/2
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"New task"}'
curl -i -X PUT http://localhost:8000/tasks/1 -H "Content-Type: application/json" -d '{"done":true}'
curl -i -X DELETE http://localhost:8000/tasks/1

# Stage 4 — one command for the whole stack
docker stop taskdb              # free port 5432 first
docker compose up               # app + db together from here on
```

## Endpoints

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/` | API info | 200 | — |
| GET | `/health` | Liveness + a real `SELECT` against Postgres | 200 | — |
| GET | `/tasks` | List all tasks | 200 | — |
| GET | `/tasks/{id}` | Get one task | 200 | 404 unknown id |
| POST | `/tasks` | Create a task | 201 | 400 missing/empty title |
| PUT | `/tasks/{id}` | Update title and/or done | 200 | 404 unknown id, 400 invalid/empty input |
| DELETE | `/tasks/{id}` | Delete a task | 204 | 404 unknown id |

Interactive docs at `http://localhost:3000/docs` once the stack is running.

## Example request

```bash
$ curl -i http://localhost:3000/tasks
HTTP/1.1 200 OK
content-type: application/json

[{"id":1,"title":"Buy groceries","done":false},
 {"id":2,"title":"Read a book","done":false},
 {"id":3,"title":"Write project report","done":true}]
```

## Persistence — how I checked it

1. Created a task, marked another one done, deleted a third — confirmed
   each change with `GET /tasks`.
2. Verified those same changes directly in `psql` (bypassing the API
   entirely), to rule out the app caching anything in memory.
3. Restarted Postgres itself (`service postgresql restart` while
   developing this / `docker compose restart db` in the containerized
   version) — the three remaining rows were still there.
4. Restarted the app process too, and hit `GET /tasks` again fresh —
   same rows, same `done` values, same missing task. The volume, not
   the running process, is what's keeping the data alive.

## Architecture — why the routes didn't change

`app/main.py` depends only on the `TaskRepository` abstract interface
(`app/repository.py`) — it never imports a concrete storage class
directly. `app/memory_repository.py` and `app/postgres_repository.py`
both implement that same interface. Swapping which one gets
constructed (`REPOSITORY_BACKEND` in `.env`) is the entire "migration"
— no route, no schema, no status code logic changed. That's the actual
point of this assignment: storage is an implementation detail sitting
behind a fixed contract, not something the rest of the app should ever
need to know about.

## Environment variables

See `.env.example`. Two keys:
- `DATABASE_URL` — connection string. Inside `docker-compose.yml` this
  is already set to use the `db` service name (not `localhost`) so the
  containers can reach each other.
- `REPOSITORY_BACKEND` — `postgres` (default, used in this submission)
  or `memory` (kept only so the in-memory version can still be run
  directly for comparison, per the assignment's "swap" requirement).

No password, host, or connection string is hardcoded anywhere in the
source — everything comes from `.env`, which is git-ignored.

## Security notes

- `.env` is git-ignored; `.env.example` (placeholder values only) is
  committed instead.
- All SQL uses parameterized placeholders (`%s`, psycopg's style) —
  user input (a title, an id) is always passed as a separate argument,
  never concatenated into the query string.
- The Postgres container's password (`dev`) is a local-dev-only
  placeholder set via environment variables in `docker-compose.yml` —
  replace it with a real secret (and stop committing even the
  placeholder to a public repo, if you change it) before this ever
  runs anywhere but your own machine.

## What's intentionally out of scope

- No authentication — matches the original CRUD spec.
- No migrations tool (Alembic, etc.) — the table is small enough that
  `CREATE TABLE IF NOT EXISTS` on startup is sufficient for this
  assignment's scope.
- No multi-stage Dockerfile / image-size optimization — noted as a
  stretch goal, not implemented here.
