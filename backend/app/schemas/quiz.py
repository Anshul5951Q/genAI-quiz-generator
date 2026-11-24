from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.question import (
    QuestionAttemptView,
    QuestionReviewResponse,
)
from app.schemas.validation import QuestionValidationSummary


class QuizGenerateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    source_text: str = Field(..., min_length=20, description="Extracted or pasted source text")
    source_type: str = Field("pasted", pattern="^(pdf|txt|pasted|pptx|ppt)$")
    source_filename: str | None = None
    num_questions: int = Field(5, ge=1, le=50)
    difficulty: str = Field("mixed", pattern="^(easy|medium|hard|mixed)$")
    topic_focus: str | None = None
    difficulty_distribution: dict[str, int] | None = None
    included_topics: list[str] | None = None
    excluded_topics: list[str] | None = None
    batch_id: str | None = None
    blueprint_config: dict | None = None
    use_demo_mode: bool = False


class QuizSummaryResponse(BaseModel):
    id: str
    title: str
    source_type: str
    source_filename: str | None = None
    question_count: int
    difficulty: str
    status: str
    approval_status: str = "draft"
    is_demo: bool
    quiz_origin: str = "document_generated"
    batch_id: str | None = None
    batch_name: str | None = None
    created_at: datetime
    latest_score_percentage: float | None = None
    latest_attempt_id: str | None = None
    attempts_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class QuizDetailResponse(BaseModel):
    id: str
    title: str
    source_type: str
    source_filename: str | None = None
    difficulty: str
    target_count: int
    topic_focus: str | None = None
    status: str
    approval_status: str = "draft"
    version: int
    is_demo: bool
    quiz_origin: str = "document_generated"
    batch_id: str | None = None
    batch_name: str | None = None
    blueprint_config: str | None = None
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionReviewResponse]
    validation_summary: QuestionValidationSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class QuizTakingResponse(BaseModel):
    id: str
    title: str
    version: int
    total_questions: int
    questions: list[QuestionAttemptView]
