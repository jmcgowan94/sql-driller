import random
import sqlite3
from datetime import date, datetime, timedelta

from app.questions import Question, question_bank

MAX_LEVEL = 10
LEVEL_UP_STREAK = 2
QUESTIONS_PER_TOPIC_PER_DAY = 1


def _ensure_topic_row(conn: sqlite3.Connection, topic: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO topic_level (topic, level, streak_correct) VALUES (?, 1, 0)",
        (topic,),
    )


def get_topic_level(conn: sqlite3.Connection, topic: str) -> tuple[int, int]:
    _ensure_topic_row(conn, topic)
    row = conn.execute(
        "SELECT level, streak_correct FROM topic_level WHERE topic = ?", (topic,)
    ).fetchone()
    return row["level"], row["streak_correct"]


def record_attempt_and_update_level(
    conn: sqlite3.Connection, question: Question, correct: bool, submitted_sql: str
) -> tuple[int, int, bool]:
    """Records the attempt and updates topic level/streak.

    A question only grants level/streak credit once per calendar day —
    once it's been answered correctly today, further submissions (right
    or wrong) are still logged but no longer mutate level/streak.

    Returns (new_level, new_streak, leveled_up).
    """
    already_credited_today = (
        conn.execute(
            "SELECT 1 FROM attempts WHERE question_id = ? AND correct = 1 "
            "AND date(timestamp) = date('now') LIMIT 1",
            (question.id,),
        ).fetchone()
        is not None
    )

    conn.execute(
        "INSERT INTO attempts (question_id, topic, difficulty, correct, submitted_sql) "
        "VALUES (?, ?, ?, ?, ?)",
        (question.id, question.topic, question.difficulty, int(correct), submitted_sql),
    )

    level, streak = get_topic_level(conn, question.topic)
    leveled_up = False
    if not already_credited_today:
        if correct:
            streak += 1
            if streak >= LEVEL_UP_STREAK and level < MAX_LEVEL:
                level += 1
                streak = 0
                leveled_up = True
        else:
            streak = 0

        conn.execute(
            "UPDATE topic_level SET level = ?, streak_correct = ? WHERE topic = ?",
            (level, streak, question.topic),
        )
    conn.commit()
    return level, streak, leveled_up


def _pick_question_for_topic(conn: sqlite3.Connection, topic: str) -> Question:
    level, _ = get_topic_level(conn, topic)
    pool = question_bank.pool_for(topic, level)
    return random.choice(pool)


_session_cache: list[Question] | None = None


def get_or_create_session(conn: sqlite3.Connection) -> list[Question]:
    global _session_cache
    if _session_cache is None:
        _session_cache = [
            _pick_question_for_topic(conn, topic) for topic in question_bank.topics()
        ]
    return _session_cache


def compute_day_streak(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT DISTINCT date(timestamp) AS d FROM attempts ORDER BY d DESC"
    ).fetchall()
    practiced_days = {datetime.strptime(r["d"], "%Y-%m-%d").date() for r in rows}
    if not practiced_days:
        return 0

    streak = 0
    cursor_day = date.today()
    if cursor_day not in practiced_days:
        cursor_day -= timedelta(days=1)
        if cursor_day not in practiced_days:
            return 0
    while cursor_day in practiced_days:
        streak += 1
        cursor_day -= timedelta(days=1)
    return streak
