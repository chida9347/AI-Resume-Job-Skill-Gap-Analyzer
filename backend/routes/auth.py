"""Account, authentication and privacy routes.

Access tokens are short-lived JWTs. Refresh tokens are opaque, stored hashed and
rotated on every use. All account deletion paths remove user-owned rows.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models.db import RefreshToken, User
from models.schemas import (
    ChangePasswordInput,
    DeleteAccountInput,
    LoginInput,
    LogoutInput,
    RefreshInput,
    RegisterInput,
    TokenPair,
    UpdateProfileInput,
    UserPublic,
)
from security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _issue_tokens(db: Session, user: User) -> TokenPair:
    settings = get_settings()
    access = create_access_token(user.id)
    raw_refresh, digest, expiry = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=digest, expires_at=expiry))
    db.commit()
    return TokenPair(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.access_token_minutes * 60,
        user=UserPublic.model_validate(user),
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, db: Session = Depends(get_db)) -> TokenPair:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        # Do not confirm which accounts exist beyond this unavoidable case.
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(db, user)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginInput, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is inactive.")
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshInput, db: Session = Depends(get_db)) -> TokenPair:
    digest = hash_token(payload.refresh_token)
    token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == digest))
    now = datetime.now(timezone.utc)
    if token is None or token.revoked or _aware(token.expires_at) <= now:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired. Sign in again.")
    user = db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Account not found or inactive.")
    # Rotation limits replay of a stolen token.
    token.revoked = True
    db.commit()
    return _issue_tokens(db, user)


@router.post("/logout")
def logout(
    payload: LogoutInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    if payload.refresh_token:
        digest = hash_token(payload.refresh_token)
        token = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == digest, RefreshToken.user_id == current.id
            )
        )
        if token:
            token.revoked = True
            db.commit()
    return {"status": "signed_out"}


@router.get("/me", response_model=UserPublic)
def me(current: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current)


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UpdateProfileInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> UserPublic:
    if payload.full_name is not None:
        current.full_name = payload.full_name.strip()
    if payload.headline is not None:
        current.headline = payload.headline.strip()
    db.commit()
    db.refresh(current)
    return UserPublic.model_validate(current)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    if not verify_password(payload.current_password, current.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(payload.new_password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password must be at most 72 bytes.")
    current.password_hash = hash_password(payload.new_password)
    # Revoke every existing refresh token after a password change.
    tokens = db.scalars(select(RefreshToken).where(RefreshToken.user_id == current.id)).all()
    for token in tokens:
        token.revoked = True
    db.commit()
    return {"status": "password_changed", "sessions_revoked": len(tokens)}


@router.delete("/me")
def delete_account(
    payload: DeleteAccountInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    if not verify_password(payload.password, current.password_hash):
        raise HTTPException(status_code=400, detail="Password is incorrect.")
    # Explicit refresh-token deletion keeps SQLite behaviour identical to
    # PostgreSQL even if foreign-key enforcement is disabled.
    tokens = db.scalars(select(RefreshToken).where(RefreshToken.user_id == current.id)).all()
    for token in tokens:
        db.delete(token)
    db.delete(current)
    db.commit()
    return {"status": "account_deleted"}
