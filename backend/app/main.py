from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app import db, difficulty
from app.judge import judge_submission
from app.models import (
    AttemptOut,
    ProgressOut,
    QueryResult,
    QuestionOut,
    SubmitRequest,
    SubmitResponse,
    TableSchema,
    TopicProgress,
)
from app.questions import question_bank

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="SQL Driller")

db.init_db()


def _question_to_out(question) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        topic=question.topic,
        difficulty=question.difficulty,
        title=question.title,
        prompt=question.prompt,
        tables=[
            TableSchema(name=t.name, ddl=t.ddl, sample_rows=t.sample_rows)
            for t in question.tables
        ],
    )


@app.get("/api/session/today", response_model=list[QuestionOut])
def get_today_session():
    conn = db.get_connection()
    try:
        questions = difficulty.get_or_create_session(conn)
    finally:
        conn.close()
    return [_question_to_out(q) for q in questions]


@app.post("/api/questions/{question_id}/submit", response_model=SubmitResponse)
def submit_answer(question_id: str, body: SubmitRequest):
    question = question_bank.get(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    result = judge_submission(question, body.sql)

    conn = db.get_connection()
    try:
        level, streak, leveled_up = difficulty.record_attempt_and_update_level(
            conn, question, result.correct, body.sql
        )
    finally:
        conn.close()

    expected = None
    reference_sql = None
    if not result.correct:
        expected = QueryResult(
            columns=question.expected_columns,
            rows=[list(r) for r in question.expected_rows],
        )
        reference_sql = question.reference_sql

    return SubmitResponse(
        correct=result.correct,
        error=result.error,
        result=QueryResult(columns=result.columns, rows=[list(r) for r in result.rows])
        if result.error is None
        else None,
        expected=expected,
        reference_sql=reference_sql,
        topic_level=level,
        topic_streak=streak,
        leveled_up=leveled_up,
    )


@app.get("/api/progress", response_model=ProgressOut)
def get_progress():
    conn = db.get_connection()
    try:
        topics = []
        for topic in question_bank.topics():
            level, streak = difficulty.get_topic_level(conn, topic)
            topics.append(TopicProgress(topic=topic, level=level, streak_correct=streak))

        day_streak = difficulty.compute_day_streak(conn)

        rows = conn.execute(
            "SELECT question_id, topic, difficulty, correct, timestamp "
            "FROM attempts ORDER BY timestamp DESC LIMIT 25"
        ).fetchall()
        recent_attempts = [
            AttemptOut(
                question_id=r["question_id"],
                topic=r["topic"],
                difficulty=r["difficulty"],
                correct=bool(r["correct"]),
                timestamp=r["timestamp"],
            )
            for r in rows
        ]
    finally:
        conn.close()

    return ProgressOut(topics=topics, day_streak=day_streak, recent_attempts=recent_attempts)


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
