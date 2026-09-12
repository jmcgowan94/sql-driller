import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import sqlparse

QUESTIONS_DIR = Path(__file__).resolve().parent.parent / "questions"


@dataclass
class TableInfo:
    name: str
    ddl: str
    sample_rows: list[dict]


@dataclass
class Question:
    id: str
    topic: str
    difficulty: int
    title: str
    prompt: str
    setup_sql: str
    reference_sql: str
    reference_sql_display: str
    order_sensitive: bool
    tables: list[TableInfo]
    expected_columns: list[str]
    expected_rows: list[tuple]


def fresh_connection(setup_sql: str) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(setup_sql)
    return conn


def _introspect_tables(conn: sqlite3.Connection) -> list[TableInfo]:
    tables: list[TableInfo] = []
    cur = conn.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    for name, ddl in cur.fetchall():
        rows_cur = conn.execute(f'SELECT * FROM "{name}" LIMIT 5')
        col_names = [d[0] for d in rows_cur.description]
        sample_rows = [dict(zip(col_names, row)) for row in rows_cur.fetchall()]
        tables.append(TableInfo(name=name, ddl=ddl, sample_rows=sample_rows))
    return tables


def _run_reference(conn: sqlite3.Connection, reference_sql: str) -> tuple[list[str], list[tuple]]:
    cur = conn.execute(reference_sql)
    columns = [d[0] for d in cur.description]
    rows = [tuple(row) for row in cur.fetchall()]
    return columns, rows


def _load_question_file(path: Path) -> Question:
    data = json.loads(path.read_text())
    conn = fresh_connection(data["setup_sql"])
    try:
        tables = _introspect_tables(conn)
        expected_columns, expected_rows = _run_reference(conn, data["reference_sql"])
    finally:
        conn.close()

    return Question(
        id=data["id"],
        topic=data["topic"],
        difficulty=int(data["difficulty"]),
        title=data["title"],
        prompt=data["prompt"],
        setup_sql=data["setup_sql"],
        reference_sql=data["reference_sql"],
        reference_sql_display=sqlparse.format(
            data["reference_sql"], reindent=True, keyword_case="upper"
        ),
        order_sensitive=bool(data.get("order_sensitive", False)),
        tables=tables,
        expected_columns=expected_columns,
        expected_rows=expected_rows,
    )


class QuestionBank:
    def __init__(self) -> None:
        self._by_id: dict[str, Question] = {}
        self._load_all()

    def _load_all(self) -> None:
        for path in sorted(QUESTIONS_DIR.rglob("*.json")):
            question = _load_question_file(path)
            if question.id in self._by_id:
                raise ValueError(f"Duplicate question id: {question.id}")
            self._by_id[question.id] = question

    def get(self, question_id: str) -> Question | None:
        return self._by_id.get(question_id)

    def topics(self) -> list[str]:
        return sorted({q.topic for q in self._by_id.values()})

    def pool_for(self, topic: str, difficulty: int) -> list[Question]:
        """Questions matching topic at exactly this difficulty, falling back
        to the closest available difficulty <= requested if none exist."""
        exact = [q for q in self._by_id.values() if q.topic == topic and q.difficulty == difficulty]
        if exact:
            return exact
        lower = [q for q in self._by_id.values() if q.topic == topic and q.difficulty < difficulty]
        if lower:
            max_lower = max(q.difficulty for q in lower)
            return [q for q in lower if q.difficulty == max_lower]
        higher = [q for q in self._by_id.values() if q.topic == topic]
        return higher

    def max_difficulty_for(self, topic: str) -> int:
        difficulties = [q.difficulty for q in self._by_id.values() if q.topic == topic]
        return max(difficulties) if difficulties else 1


# Loaded once at process start; question bank is static file content.
question_bank = QuestionBank()
