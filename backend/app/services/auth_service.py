"""
Authentication service: user CRUD, login, token management.
"""
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import UserModel


class AuthServiceError(Exception):
    """User-safe authentication error."""


class AuthService:
    @classmethod
    def create_user(
        cls,
        db: Session,
        email: str,
        password: str,
        full_name: str | None = None,
        role: str = "STUDENT",
    ) -> UserModel:
        email = email.strip().lower()
        if not email or "@" not in email:
            raise AuthServiceError("Please provide a valid email address.")
        if len(password) < 8:
            raise AuthServiceError("Password must be at least 8 characters long.")
        if role not in ("ADMIN", "STUDENT", "RECRUITER", "INTERVIEWER"):
            raise AuthServiceError(f"Invalid role '{role}'.")

        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            raise AuthServiceError("An account with this email address already exists.")

        user = UserModel(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user registered: {email} (role={role})")
        return user

    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> UserModel:
        email = email.strip().lower()
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise AuthServiceError("Invalid email or password.")
        if not user.is_active:
            raise AuthServiceError("This account has been deactivated. Please contact an administrator.")
        return user

    @classmethod
    def generate_tokens(cls, user: UserModel) -> dict:
        payload = {"sub": user.id, "email": user.email, "role": user.role}
        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token(payload),
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            },
        }

    @classmethod
    def get_user_by_id(cls, db: Session, user_id: str) -> UserModel | None:
        return db.query(UserModel).filter(UserModel.id == user_id, UserModel.is_active == True).first()

    @classmethod
    def list_users(cls, db: Session) -> list[UserModel]:
        return db.query(UserModel).order_by(UserModel.created_at.desc()).all()

    @classmethod
    def update_user_role(cls, db: Session, user_id: str, new_role: str) -> UserModel:
        if new_role not in ("ADMIN", "STUDENT", "RECRUITER", "INTERVIEWER"):
            raise AuthServiceError(f"Invalid role: {new_role}")
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise AuthServiceError("User not found.")
        user.role = new_role
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def deactivate_user(cls, db: Session, user_id: str) -> UserModel:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise AuthServiceError("User not found.")
        user.is_active = False
        db.commit()
        db.refresh(user)
        return user
