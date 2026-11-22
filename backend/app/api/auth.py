"""Authentication endpoints (JWT bearer)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginRequest, Token, UserOut
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Simple in-memory brute-force guard: throttle repeated login failures per
# client IP + email. Good enough for a single-process deployment.
_MAX_FAILURES = 5
_WINDOW_SECONDS = 900  # 15 minutes
_failures: dict[str, list[float]] = defaultdict(list)
_fail_lock = Lock()


def _attempt_key(request: Request, email: str) -> str:
    ip = request.client.host if request.client else "unknown"
    return f"{ip}|{email.strip().lower()}"


def _is_throttled(key: str) -> bool:
    now = monotonic()
    with _fail_lock:
        recent = [t for t in _failures[key] if now - t < _WINDOW_SECONDS]
        _failures[key] = recent
        return len(recent) >= _MAX_FAILURES


def _record_failure(key: str) -> None:
    now = monotonic()
    with _fail_lock:
        _failures[key].append(now)


def _clear_failures(key: str) -> None:
    with _fail_lock:
        _failures.pop(key, None)


@router.post("/login", response_model=Token)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    key = _attempt_key(request, payload.email)
    if _is_throttled(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="محاولات دخول كثيرة جداً. حاول مرة أخرى بعد قليل.",
        )
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        _record_failure(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="الحساب معطّل")
    _clear_failures(key)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(str(user.id), user.role.value)
    return Token(access_token=token, role=user.role.value, full_name=user.full_name)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
