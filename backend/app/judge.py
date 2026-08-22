import sqlite3
from collections import Counter
from dataclasses import dataclass

from app.questions import Question, fresh_connection


@dataclass
class JudgeResult:
    correct: bool
    error: str | None
    columns: list[str]
    rows: list[tuple]


def _rows_match(expected: list[tuple], actual: list[tuple], order_sensitive: bool) -> bool:
    if order_sensitive:
        return expected == actual
    return Counter(expected) == Counter(actual)


def judge_submission(question: Question, submitted_sql: str) -> JudgeResult:
    conn = fresh_connection(question.setup_sql)
    try:
        cur = conn.execute(submitted_sql)
        if cur.description is None:
            return JudgeResult(
                correct=False,
                error="Query did not return any rows (not a SELECT statement?).",
                columns=[],
                rows=[],
            )
        columns = [d[0] for d in cur.description]
        rows = [tuple(row) for row in cur.fetchall()]
    except sqlite3.Error as exc:
        return JudgeResult(correct=False, error=str(exc), columns=[], rows=[])
    finally:
        conn.close()

    correct = _rows_match(question.expected_rows, rows, question.order_sensitive)
    return JudgeResult(correct=correct, error=None, columns=columns, rows=rows)
