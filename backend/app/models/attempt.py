import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class QuizAttemptModel(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(
        String(36),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    publication_id = Column(
        String(36),
        ForeignKey("quiz_publications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    batch_id = Column(
        String(36),
        ForeignKey("batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    learner_name = Column(String(255), nullable=True)
    learner_email = Column(String(255), nullable=True, index=True)
    learner_id = Column(String(100), nullable=True)
    version_label = Column(String(10), nullable=False, default="A")  # "A", "B", "C"
    quiz_version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="in_progress")  # "in_progress", "completed"
    score = Column(Integer, nullable=False, default=0)
    total_questions = Column(Integer, nullable=False, default=0)
    unanswered_count = Column(Integer, nullable=False, default=0)
    score_percentage = Column(Float, nullable=False, default=0.0)
    marks_obtained = Column(Float, nullable=False, default=0.0)
    total_marks = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    quiz = relationship("QuizModel", back_populates="attempts")
    publication = relationship("PublicationModel", back_populates="attempts")
    answers = relationship("AttemptAnswerModel", back_populates="attempt", cascade="all, delete-orphan")


class AttemptAnswerModel(Base):
    __tablename__ = "attempt_answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = Column(
        String(36),
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected_option_id = Column(String(36), nullable=True)  # Null if question was left unanswered
    is_correct = Column(Boolean, nullable=False, default=False)

    attempt = relationship("QuizAttemptModel", back_populates="answers")
