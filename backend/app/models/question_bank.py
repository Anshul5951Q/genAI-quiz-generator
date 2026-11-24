import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class QuestionBankEntryModel(Base):
    """
    Stores approved questions across all generated quizzes in a searchable repository.
    Enables reuse tracking and prevent repeating questions to the same Batch.
    """

    __tablename__ = "question_bank"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)  # JSON array of options
    explanation = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False, default="General")
    difficulty = Column(String(20), nullable=False, default="medium")
    question_style = Column(String(50), nullable=False, default="recall")
    source_filename = Column(String(255), nullable=True)
    validation_verdict = Column(String(20), nullable=False, default="pass")
    times_used = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_used_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    usages = relationship(
        "QuestionUsageModel",
        back_populates="question_entry",
        cascade="all, delete-orphan",
    )


class QuestionUsageModel(Base):
    """Tracks every time a QuestionBank item is assigned to a Quiz or Batch."""

    __tablename__ = "question_usages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_bank_id = Column(
        String(36),
        ForeignKey("question_bank.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quiz_id = Column(
        String(36),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id = Column(
        String(36),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    used_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    question_entry = relationship("QuestionBankEntryModel", back_populates="usages")
