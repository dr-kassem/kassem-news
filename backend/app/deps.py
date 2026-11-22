"""FastAPI dependencies: authentication, RBAC and pagination."""
from __future__ import annotations

from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_ROLE_RANK = {Role.viewer: 0, Role.reviewer: 1, Role.editor: 2, Role.admin: 3}


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="بيانات الاعتماد غير صالحة",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_exc
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or not user.is_active:
        raise credentials_exc
    return user


def require_role(minimum: Role):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if _ROLE_RANK[user.role] < _ROLE_RANK[minimum]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="لا تملك الصلاحية الكافية لهذا الإجراء",
            )
        return user

    return _checker


class Pagination:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(page, 1)
        self.page_size = min(max(page_size, 1), 100)
        self.offset = (self.page - 1) * self.page_size
        self.limit = self.page_size


def get_pagination(page: int = 1, page_size: int = 20) -> Pagination:
    return Pagination(page=page, page_size=page_size)
