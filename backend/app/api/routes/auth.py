from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user, require_admin
from app.core.security import decode_token
from app.db.session import get_db
from app.services.auth_service import AuthService, AuthServiceError

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None
    role: str = "STUDENT"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict


class UpdateRoleRequest(BaseModel):
    role: str


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new user account and return JWT tokens."""
    try:
        user = AuthService.create_user(
            db,
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            role=req.role,
        )
        return AuthService.generate_tokens(user)
    except AuthServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return JWT access + refresh tokens."""
    try:
        user = AuthService.authenticate(db, req.email, req.password)
        return AuthService.generate_tokens(user)
    except AuthServiceError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for new access + refresh tokens."""
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")
    user = AuthService.get_user_by_id(db, payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return AuthService.generate_tokens(user)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user=Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


# --- Admin user management ---

@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    """List all users. Admin only."""
    return AuthService.list_users(db)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_role(user_id: str, req: UpdateRoleRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Update a user's role. Admin only."""
    try:
        return AuthService.update_user_role(db, user_id, req.role)
    except AuthServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(user_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Deactivate a user account. Admin only."""
    try:
        return AuthService.deactivate_user(db, user_id)
    except AuthServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
