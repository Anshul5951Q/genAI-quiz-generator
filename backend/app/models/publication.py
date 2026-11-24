import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class PublicationModel(Base):
    """
    Represents an approved quiz published for learners to take online.
    Can be assigned to a specific Batch or distributed via a shareable access code.
    """

    __tablename__ = "quiz_publications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(
        String(36),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id = Column(
        String(36),
        ForeignKey("batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    access_code = Column(String(32), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")  # "active", "closed", "scheduled"
    time_limit_minutes = Column(Integer, nullable=True)  # Null if untimed
    max_attempts = Column(Integer, nullable=False, default=1)
    shuffle_questions = Column(Boolean, nullable=False, default=True)
    shuffle_options = Column(Boolean, nullable=False, default=True)
    show_explanations_after = Column(Boolean, nullable=False, default=True)
    passing_percentage = Column(Float, nullable=False, default=50.0)
    marks_per_question = Column(Float, nullable=False, default=1.0)
    negative_marking_per_question = Column(Float, nullable=False, default=0.0)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    quiz = relationship("QuizModel", back_populates="publications")
    batch = relationship("BatchModel", back_populates="publications")
    attempts = relationship("QuizAttemptModel", back_populates="publication")
