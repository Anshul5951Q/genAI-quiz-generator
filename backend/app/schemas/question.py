from pydantic import BaseModel, ConfigDict, Field

# --- Option Schemas ---


class OptionBase(BaseModel):
    option_letter: str = Field(..., pattern="^[A-D]$", description="Letter A, B, C, or D")
    option_text: str = Field(..., min_length=1)


class OptionCreate(OptionBase):
    id: str | None = None
    is_correct: bool = False


class OptionUpdate(BaseModel):
    id: str | None = None
    option_letter: str
    option_text: str
    is_correct: bool


class OptionReviewResponse(OptionBase):
    id: str
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)


class OptionAttemptView(OptionBase):
    """Secure view of options sent to quiz takers. Never contains is_correct."""

    id: str

    model_config = ConfigDict(from_attributes=True)


# --- Question Schemas ---


class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=5)
    explanation: str = Field(..., min_length=5)
    evidence: str = Field(..., min_length=5)
    source_page: int | None = None
    topic: str = "General"
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    question_style: str = "recall"
    distractor_rationale: str | None = None


class QuestionCreate(QuestionBase):
    id: str | None = None
    options: list[OptionCreate]
    validation_status: str = "review"
    validation_issues: list[str] = []
    order_index: int = 0


class QuestionUpdate(BaseModel):
    question_text: str | None = None
    explanation: str | None = None
    evidence: str | None = None
    source_page: int | None = None
    topic: str | None = None
    difficulty: str | None = None
    distractor_rationale: str | None = None
    options: list[OptionUpdate] | None = None
    validation_status: str | None = None


class QuestionReviewResponse(QuestionBase):
    """Full question details for the creator/reviewer before publishing/taking."""

    id: str
    quiz_id: str
    validation_status: str
    validation_issues: list[str]
    order_index: int
    options: list[OptionReviewResponse]

    model_config = ConfigDict(from_attributes=True)


class QuestionAttemptView(BaseModel):
    """Safe schema for students taking the quiz. Correct answers and explanations are omitted."""

    id: str
    question_text: str
    order_index: int
    options: list[OptionAttemptView]

    model_config = ConfigDict(from_attributes=True)


class QuestionResultResponse(BaseModel):
    """Detailed question result returned only after quiz submission."""

    id: str
    question_text: str
    order_index: int
    topic: str
    difficulty: str
    explanation: str
    evidence: str
    source_page: int | None = None
    options: list[OptionReviewResponse]
    selected_option_id: str | None = None
    correct_option_id: str
    is_correct: bool
