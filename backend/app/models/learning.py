import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.db.session import Base


class SkillProfileModel(Base):
    """Aggregated skill proficiency profile for a user based on interview history."""

    __tablename__ = "skill_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False)
    skill_category = Column(String(50), nullable=False, default="technical")
    proficiency_score = Column(Float, nullable=False, default=0.0)  # 0-100
    attempts_count = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class LearningRecommendationModel(Base):
    """Personalized learning topic recommendation based on weak areas."""

    __tablename__ = "learning_recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=1)  # 1=high, 2=medium, 3=low
    resources_json = Column(Text, nullable=True)   # JSON array of resource links/titles
    is_completed = Column(Boolean, nullable=False, default=False)
    source_session_id = Column(String(36), nullable=True)  # Interview session that triggered this
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class AIModelLogModel(Base):
    """Log of every AI model invocation for performance monitoring."""

    __tablename__ = "ai_model_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(50), nullable=False, default="unknown")   # ollama, gemini, groq, demo
    model_name = Column(String(100), nullable=True)
    task_type = Column(String(100), nullable=True)  # resume_extraction, question_generation, evaluation, etc.
    prompt_length = Column(Integer, nullable=True)
    response_length = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class AuditLogModel(Base):
    """Security audit trail for administrative and sensitive operations."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)         # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String(50), nullable=True)    # quiz, resume, interview, user, etc.
    resource_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)                # JSON with extra context
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
