from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.question import QuestionResultResponse


class AttemptCreateResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    quiz_title: str
    quiz_version: int
    total_questions: int
    started_at: datetime


class AnswerSubmissionItem(BaseModel):
    question_id: str
    selected_option_id: str | None = None


class AttemptSubmissionRequest(BaseModel):
    answers: list[AnswerSubmissionItem] = Field(..., description="User selected answers for each question")


class ScoreBreakdownItem(BaseModel):
    category: str
    total: int
    correct: int
    percentage: float


class AttemptResultResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    quiz_title: str
    started_at: datetime
    completed_at: datetime
    score: int
    total_questions: int
    unanswered_count: int
    score_percentage: float
    difficulty_breakdown: list[ScoreBreakdownItem] = []
    topic_breakdown: list[ScoreBreakdownItem] = []
    questions: list[QuestionResultResponse] = []
