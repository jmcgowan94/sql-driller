from pydantic import BaseModel


class TableSchema(BaseModel):
    name: str
    ddl: str
    sample_rows: list[dict]


class QuestionOut(BaseModel):
    id: str
    topic: str
    difficulty: int
    title: str
    prompt: str
    tables: list[TableSchema]


class SubmitRequest(BaseModel):
    sql: str


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list]


class SubmitResponse(BaseModel):
    correct: bool
    error: str | None = None
    result: QueryResult | None = None
    expected: QueryResult | None = None
    reference_sql: str | None = None
    topic_level: int
    topic_streak: int
    leveled_up: bool


class TopicProgress(BaseModel):
    topic: str
    level: int
    streak_correct: int


class AttemptOut(BaseModel):
    question_id: str
    topic: str
    difficulty: int
    correct: bool
    timestamp: str


class ProgressOut(BaseModel):
    topics: list[TopicProgress]
    day_streak: int
    recent_attempts: list[AttemptOut]
