from pydantic import BaseModel, Field


class DifficultyDistribution(BaseModel):
    easy: int = Field(default=0, ge=0)
    medium: int = Field(default=0, ge=0)
    hard: int = Field(default=0, ge=0)


class TopicCoverageItem(BaseModel):
    topic: str
    chunk_mentions: int = 0
    allocated_questions: int = 0
    difficulty_breakdown: dict[str, int] = {}
    coverage_status: str = "adequate"  # adequate, underrepresented, insufficient
    notes: str | None = None


class ExamBlueprint(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    total_questions: int = Field(..., ge=1, le=50)
    difficulty_distribution: DifficultyDistribution
    included_topics: list[str] = []
    excluded_topics: list[str] = []
    question_styles: list[str] = ["recall", "application", "comparison", "case_based"]
    marks_per_question: float = Field(default=1.0, gt=0)
    negative_marking_per_question: float = Field(default=0.0, ge=0)
    time_limit_minutes: int | None = Field(default=None, ge=1, le=240)
    batch_id: str | None = None
    show_explanations_after: bool = True
    passing_percentage: float = 50.0


class BlueprintValidationResult(BaseModel):
    is_valid: bool
    issues: list[str] = []
    warnings: list[str] = []
    coverage_matrix: list[TopicCoverageItem] = []
    extracted_topics: list[str] = []
