from pydantic import BaseModel, Field


class DeterministicCheckResult(BaseModel):
    is_valid: bool
    issues: list[str] = []
    normalized_evidence: str | None = None


class SemanticValidationResult(BaseModel):
    supported_by_source: bool = Field(
        ...,
        description="Whether the cited evidence strictly supports the proposed answer",
    )
    single_best_answer: bool = Field(..., description="Whether exactly one answer is defensibly correct")
    distractors_valid: bool = Field(..., description="Whether distractors are genuinely incorrect and plausible")
    explanation_valid: bool = Field(..., description="Whether explanation matches source facts")
    ambiguity_detected: bool = Field(..., description="Whether the stem or options contain ambiguity")
    verdict: str = Field(..., pattern="^(PASS|REVIEW|REJECT)$", description="PASS, REVIEW, or REJECT")
    issues: list[str] = Field(default_factory=list, description="Concise diagnostic issues")


class QuestionValidationSummary(BaseModel):
    total_generated: int = 0
    passed_count: int = 0
    flagged_review_count: int = 0
    regenerated_count: int = 0
    rejected_count: int = 0


class ValidationDetail(BaseModel):
    question_id: str
    status: str  # "pass", "review", "reject"
    deterministic_passed: bool
    semantic_verdict: str | None = None
    issues: list[str] = []
