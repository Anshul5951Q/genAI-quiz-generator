import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.db.session import Base


class UserModel(Base):
    """
    Authenticated user account with role-based access control.
    Roles: ADMIN, STUDENT, RECRUITER, INTERVIEWER
    """

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(32), nullable=False, default="STUDENT")  # ADMIN, STUDENT, RECRUITER, INTERVIEWER
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
