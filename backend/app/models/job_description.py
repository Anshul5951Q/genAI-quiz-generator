import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.db.session import Base


class JobDescriptionModel(Base):
    """Job description with requirements for interview targeting."""

    __tablename__ = "job_descriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    content_text = Column(Text, nullable=False)        # Original full JD text
    file_path = Column(String(512), nullable=True)     # If uploaded as file
    status = Column(String(20), nullable=False, default="uploaded")  # uploaded, extracted, failed
    # Extracted fields
    experience_min_years = Column(Integer, nullable=True)
    experience_max_years = Column(Integer, nullable=True)
    education_requirement = Column(Text, nullable=True)
    required_skills_json = Column(Text, nullable=True)   # JSON array
    preferred_skills_json = Column(Text, nullable=True)  # JSON array
    responsibilities_json = Column(Text, nullable=True)  # JSON array
    domain_knowledge_json = Column(Text, nullable=True)  # JSON array
    soft_skills_json = Column(Text, nullable=True)       # JSON array
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class JDRequirementModel(Base):
    """Individual requirement line extracted from a JD."""

    __tablename__ = "jd_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    jd_id = Column(String(36), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="technical")  # technical, experience, education, soft, preferred
    is_required = Column(Boolean, nullable=False, default=True)


class ResumeJDMatchModel(Base):
    """Cached resume-JD compatibility analysis result."""

    __tablename__ = "resume_jd_matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    jd_id = Column(String(36), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    compatibility_score = Column(Float, nullable=False, default=0.0)  # 0-100
    matching_skills_json = Column(Text, nullable=True)   # JSON array
    missing_skills_json = Column(Text, nullable=True)    # JSON array
    weak_areas_json = Column(Text, nullable=True)        # JSON array
    recommendations_json = Column(Text, nullable=True)   # JSON array of learning topics
    interview_focus_json = Column(Text, nullable=True)   # JSON array of suggested focus areas
    full_analysis_json = Column(Text, nullable=True)     # Full structured analysis
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
