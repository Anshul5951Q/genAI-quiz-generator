import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class QuizVersionMappingModel(Base):
    """
    Stores randomized question and option order mappings for parallel exam versions (A, B, C).
    Preserves exact option-to-correctness relationships and history.
    """

    __tablename__ = "quiz_version_mappings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(
        String(36),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_label = Column(String(10), nullable=False)  # "A", "B", "C"
    question_order_json = Column(Text, nullable=False)  # JSON array of question IDs
    option_order_json = Column(Text, nullable=False)    # JSON dict mapping question_id -> list of option IDs
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    quiz = relationship("QuizModel", back_populates="version_mappings")
