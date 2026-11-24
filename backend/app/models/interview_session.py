import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.db.session import Base


class InterviewSessionModel(Base):
    """An active or completed interview session for a user."""

    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="in_progress")  # in_progress, completed, abandoned
    current_question_index = Column(Integer, nullable=False, default=0)
    total_score = Column(Float, nullable=False, default=0.0)
    max_possible_score = Column(Float, nullable=False, default=0.0)
    score_percentage = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    # Serialized adaptive state: tracks difficulty adjustments
    adaptive_state_json = Column(Text, nullable=True)


class InterviewResponseModel(Base):
    """A candidate's answer to a single interview question."""

    __tablename__ = "interview_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text = Column(Text, nullable=True)       # Null if skipped
    code_answer = Column(Text, nullable=True)       # For coding questions
    time_taken_seconds = Column(Integer, nullable=False, default=0)
    is_skipped = Column(Boolean, nullable=False, default=False)
    is_follow_up = Column(Boolean, nullable=False, default=False)
    parent_response_id = Column(String(36), nullable=True)  # For follow-up chains
    submitted_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class AnswerEvaluationModel(Base):
    """AI evaluation result for a single interview response."""

    __tablename__ = "answer_evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    response_id = Column(String(36), ForeignKey("interview_responses.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    # Criterion scores (raw 0-10 scale)
    technical_accuracy_score = Column(Float, nullable=False, default=0.0)
    conceptual_understanding_score = Column(Float, nullable=False, default=0.0)
    completeness_score = Column(Float, nullable=False, default=0.0)
    clarity_score = Column(Float, nullable=False, default=0.0)
    practical_examples_score = Column(Float, nullable=False, default=0.0)
    # Weighted final score (0-10 scale)
    final_score = Column(Float, nullable=False, default=0.0)
    max_score = Column(Float, nullable=False, default=10.0)
    # Detailed feedback
    correct_concepts_json = Column(Text, nullable=True)   # JSON array of correctly mentioned concepts
    missing_concepts_json = Column(Text, nullable=True)   # JSON array of missing concepts
    incorrect_statements_json = Column(Text, nullable=True)  # JSON array of wrong claims
    strengths_json = Column(Text, nullable=True)          # JSON array of strengths
    weaknesses_json = Column(Text, nullable=True)         # JSON array of weaknesses
    suggested_improvement = Column(Text, nullable=True)
    model_confidence = Column(Float, nullable=False, default=0.0)  # 0.0-1.0
    evaluation_provider = Column(String(50), nullable=True)  # ollama, gemini, groq
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
