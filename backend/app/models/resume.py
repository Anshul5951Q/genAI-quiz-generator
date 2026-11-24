import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.db.session import Base


class ResumeModel(Base):
    """Uploaded resume file reference and processing status."""

    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    file_type = Column(String(20), nullable=False, default="pdf")  # pdf, docx
    status = Column(String(20), nullable=False, default="uploaded")  # uploaded, processing, extracted, failed
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class ResumeExtractionModel(Base):
    """AI-extracted structured content from a resume."""

    __tablename__ = "resume_extractions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    education_json = Column(Text, nullable=True)       # JSON array
    experience_json = Column(Text, nullable=True)      # JSON array
    internships_json = Column(Text, nullable=True)     # JSON array
    certifications_json = Column(Text, nullable=True)  # JSON array
    achievements_json = Column(Text, nullable=True)    # JSON array
    programming_languages_json = Column(Text, nullable=True)  # JSON array of strings
    frameworks_json = Column(Text, nullable=True)      # JSON array
    databases_json = Column(Text, nullable=True)       # JSON array
    tools_json = Column(Text, nullable=True)           # JSON array
    raw_extraction_json = Column(Text, nullable=True)  # Full raw LLM output
    extraction_confidence = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class ResumeSkillModel(Base):
    """Normalized skill record extracted from a resume."""

    __tablename__ = "resume_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False)
    skill_category = Column(String(50), nullable=False, default="technical")  # technical, soft, domain, tool
    proficiency_level = Column(String(20), nullable=True)  # beginner, intermediate, advanced, expert


class ResumeProjectModel(Base):
    """Individual project extracted from a resume with deep intelligence."""

    __tablename__ = "resume_projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)
    technologies_json = Column(Text, nullable=True)   # JSON array of tech names
    architecture = Column(Text, nullable=True)
    candidate_contribution = Column(Text, nullable=True)
    key_features_json = Column(Text, nullable=True)   # JSON array
    achievements = Column(Text, nullable=True)
    concepts_json = Column(Text, nullable=True)       # JSON array of technical concepts
    order_index = Column(Integer, nullable=False, default=0)
