# SQL Driller

A small local web app for daily SQL practice. Runs entirely on your machine — SQLite for
the drill questions, a local SQLite file for your progress. Nothing leaves your computer.

## Setup (one time)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
cd backend
source .venv/bin/activate   # if not already active
uvicorn app.main:app --reload --port 8000
```

Then open http://localhost:8000

## How it works

- Each time you start the server you get one question per topic (filtering,
  aggregation, joins, subqueries, window functions, CTEs), picked to match your
  current level in that topic. The set stays the same until you restart the
  server.
- Write a SQL query in the editor and click **Run & Check** — it runs against a real
  in-memory SQLite database seeded for that question and compares your result to the
  expected answer.
- Get 2 correct in a row on a topic and it levels up (max level 5) — future days pull
  harder questions for that topic. A wrong answer resets the streak-to-level-up but never
  drops your level, so mistakes don't set you back, they just pause progress until you
  get it right.
- The **Progress** page shows your day streak, per-topic level, and recent attempt history.

## Adding more questions

Drop a new JSON file into `backend/questions/<topic>/`, e.g.:

```json
{
  "id": "joins_7",
  "topic": "joins",
  "difficulty": 2,
  "title": "...",
  "prompt": "...",
  "setup_sql": "CREATE TABLE ...; INSERT INTO ...;",
  "reference_sql": "SELECT ...",
  "order_sensitive": false
}
```

`setup_sql` creates and seeds the tables; `reference_sql` is the correct-answer query
used to compute the expected result (never shown to you, only its output on a wrong
answer). Set `order_sensitive: true` if the question specifically requires `ORDER BY`.
Restart the server to pick up new files.
