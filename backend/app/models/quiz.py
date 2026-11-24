import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class QuizModel(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    source_type = Column(String(20), nullable=False)  # "pdf", "txt", "pasted"
    source_filename = Column(String(255), nullable=True)
    source_text_length = Column(Integer, nullable=False, default=0)
    difficulty = Column(String(20), nullable=False, default="mixed")
    target_count = Column(Integer, nullable=False, default=5)
    topic_focus = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="draft")  # "draft", "published"
    approval_status = Column(String(20), nullable=False, default="draft")  # "draft", "under_review", "approved", "published"
    version = Column(Integer, nullable=False, default=1)
    is_demo = Column(Boolean, nullable=False, default=False)
    quiz_origin = Column(String(32), nullable=False, default="document_generated")  # "demo", "document_generated"
    batch_id = Column(String(36), ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    blueprint_config = Column(Text, nullable=True)  # JSON string of exam blueprint coverage planning
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    batch = relationship("BatchModel", back_populates="quizzes")
    questions = relationship(
        "QuestionModel",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuestionModel.order_index",
    )
    attempts = relationship("QuizAttemptModel", back_populates="quiz", cascade="all, delete-orphan")
    publications = relationship(
        "PublicationModel",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )
    version_mappings = relationship(
        "QuizVersionMappingModel",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )


class QuestionModel(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(
        String(36),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True)
    topic = Column(String(100), nullable=False, default="General")
    difficulty = Column(String(20), nullable=False, default="medium")
    question_style = Column(String(50), nullable=False, default="recall")  # recall, application, comparison, case_based, error_analysis
    distractor_rationale = Column(Text, nullable=True)
    validation_status = Column(String(20), nullable=False, default="review")  # "pass", "review", "reject"
    validation_issues = Column(Text, nullable=False, default="[]")  # JSON string
    semantic_details = Column(Text, nullable=True)  # JSON string
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    quiz = relationship("QuizModel", back_populates="questions")
    options = relationship(
        "OptionModel",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="OptionModel.option_letter",
    )


class OptionModel(Base):
    __tablename__ = "options"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_letter = Column(String(2), nullable=False)  # "A", "B", "C", "D"
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)

    question = relationship("QuestionModel", back_populates="options")
