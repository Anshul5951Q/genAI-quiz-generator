import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.db.session import Base


class InterviewModel(Base):
    """Interview configuration created by user."""

    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    jd_id = Column(String(36), ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    job_role = Column(String(255), nullable=True)
    experience_level = Column(String(50), nullable=False, default="fresher")  # fresher, 0-2, 2-5, 5+
    categories_json = Column(Text, nullable=True)       # JSON array: ["technical", "hr", "project-based"]
    difficulty = Column(String(20), nullable=False, default="medium")  # easy, medium, hard, adaptive
    num_questions = Column(Integer, nullable=False, default=15)
    duration_minutes = Column(Integer, nullable=True)
    num_rounds = Column(Integer, nullable=False, default=1)
    difficulty_distribution_json = Column(Text, nullable=True)  # JSON: {"easy": 30, "medium": 40, "hard": 30}
    custom_instructions = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft")  # draft, generating, ready, archived
    generation_progress = Column(Integer, nullable=False, default=0)  # 0-100 percentage
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class InterviewRoundModel(Base):
    """An individual round within an interview."""

    __tablename__ = "interview_rounds"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    round_number = Column(Integer, nullable=False, default=1)
    round_name = Column(String(100), nullable=False)
    round_type = Column(String(50), nullable=False, default="technical")  # technical, hr, coding, project, aptitude


class InterviewQuestionModel(Base):
    """
    A generated interview question with full context for evaluation.
    Grounded in resume/JD evidence.
    """

    __tablename__ = "interview_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    round_id = Column(String(36), ForeignKey("interview_rounds.id", ondelete="CASCADE"), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="technical")
    difficulty = Column(String(20), nullable=False, default="medium")
    related_skill = Column(String(100), nullable=True)
    source_type = Column(String(30), nullable=False, default="general_technical")
    # resume-based, jd-based, general_technical, project-based, behavioural
    source_evidence = Column(Text, nullable=True)       # Quote from resume/JD supporting this question
    expected_concepts_json = Column(Text, nullable=True) # JSON array of key concepts for good answer
    rubric_json = Column(Text, nullable=True)           # JSON rubric for evaluation
    max_score = Column(Integer, nullable=False, default=10)
    suggested_time_seconds = Column(Integer, nullable=False, default=120)
    is_follow_up_eligible = Column(Integer, nullable=False, default=1)  # 1=True, 0=False
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
