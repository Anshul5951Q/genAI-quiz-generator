from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.question import OptionAttemptView

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class PublicationCreate(BaseModel):
    quiz_id: str
    batch_id: str | None = None
    access_code: str | None = Field(default=None, min_length=4, max_length=32)
    time_limit_minutes: int | None = Field(default=None, ge=1, le=240)
    max_attempts: int = Field(default=1, ge=1, le=10)
    shuffle_questions: bool = True
    shuffle_options: bool = True
    show_explanations_after: bool = True
    passing_percentage: float = Field(default=50.0, ge=0.0, le=100.0)
    marks_per_question: float = Field(default=1.0, gt=0.0)
    negative_marking_per_question: float = Field(default=0.0, ge=0.0)
    start_time: datetime | None = None
    end_time: datetime | None = None
    instructions: str | None = Field(default=None, max_length=2000)


class PublicationUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(active|closed|scheduled)$")
    time_limit_minutes: int | None = Field(default=None, ge=1, le=240)
    max_attempts: int | None = Field(default=None, ge=1, le=10)
    show_explanations_after: bool | None = None
    instructions: str | None = Field(default=None, max_length=2000)


class PublicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quiz_id: str
    quiz_title: str
    batch_id: str | None = None
    batch_name: str | None = None
    access_code: str
    status: str
    time_limit_minutes: int | None = None
    max_attempts: int = 1
    shuffle_questions: bool = True
    shuffle_options: bool = True
    show_explanations_after: bool = True
    passing_percentage: float = 50.0
    marks_per_question: float = 1.0
    negative_marking_per_question: float = 0.0
    start_time: datetime | None = None
    end_time: datetime | None = None
    instructions: str | None = None
    created_at: datetime
    submissions_count: int = 0
    average_score_percentage: float | None = None


# --- Secure Student Assessment Schemas (Zero Answer Key Leakage) ---


class StudentQuestionItem(BaseModel):
    id: str
    question_text: str
    order_index: int
    options: list[OptionAttemptView]  # id, option_letter, option_text only


class StudentAssessmentView(BaseModel):
    publication_id: str
    access_code: str
    quiz_title: str
    time_limit_minutes: int | None = None
    total_questions: int
    marks_per_question: float
    negative_marking_per_question: float
    instructions: str | None = None
    questions: list[StudentQuestionItem]


class StudentAttemptStartRequest(BaseModel):
    learner_name: str = Field(..., min_length=1, max_length=255)
    learner_email: str = Field(..., pattern=EMAIL_REGEX)
    learner_id: str | None = Field(default=None, max_length=100)


class StudentAttemptStartResponse(BaseModel):
    attempt_id: str
    publication_id: str
    started_at: datetime
    expires_at: datetime | None = None
    server_time: datetime


class StudentAnswerItem(BaseModel):
    question_id: str
    selected_option_id: str | None = None  # None for unanswered


class StudentAttemptSubmitRequest(BaseModel):
    attempt_id: str
    answers: list[StudentAnswerItem]


class StudentOptionResult(BaseModel):
    id: str
    option_letter: str
    option_text: str
    is_correct: bool


class StudentQuestionResult(BaseModel):
    id: str
    question_text: str
    order_index: int
    explanation: str
    evidence: str
    source_page: int | None = None
    selected_option_id: str | None = None
    correct_option_id: str
    is_correct: bool
    options: list[StudentOptionResult]


class StudentAttemptResultResponse(BaseModel):
    attempt_id: str
    quiz_title: str
    score: int
    total_questions: int
    unanswered_count: int
    score_percentage: float
    marks_obtained: float
    total_marks: float
    passed: bool
    completed_at: datetime
    show_explanations: bool
    question_results: list[StudentQuestionResult] | None = None
