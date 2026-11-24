import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class BatchModel(Base):
    """
    Represents an instructional cohort or group of learners.
    Strictly referred to as 'Batch' throughout the application.
    """

    __tablename__ = "batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    join_code = Column(String(32), unique=True, nullable=False, index=True)
    is_archived = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    members = relationship(
        "BatchMembershipModel",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="BatchMembershipModel.joined_at",
    )
    publications = relationship(
        "PublicationModel",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    quizzes = relationship(
        "QuizModel",
        back_populates="batch",
    )


class BatchMembershipModel(Base):
    """Represents an enrolled learner within a specific Batch."""

    __tablename__ = "batch_memberships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(
        String(36),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    learner_name = Column(String(255), nullable=False)
    learner_email = Column(String(255), nullable=False, index=True)
    learner_id = Column(String(100), nullable=True)  # Optional institutional student ID
    joined_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    batch = relationship("BatchModel", back_populates="members")
