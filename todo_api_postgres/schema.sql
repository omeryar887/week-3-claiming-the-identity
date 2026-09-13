-- schema.sql
--
-- Reference copy of the table the app creates automatically on startup
-- (see app/postgres_repository.py, _ensure_schema). Not required to run
-- this manually — it's here so the table shape is reviewable without
-- reading Python, and so you can run it by hand if you ever want to
-- inspect or recreate the table outside the app.

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);

-- Seed data (the app only inserts these if the table is empty):
-- INSERT INTO tasks (title, done) VALUES
--   ('Buy groceries', FALSE),
--   ('Read a book', FALSE),
--   ('Write project report', TRUE);
