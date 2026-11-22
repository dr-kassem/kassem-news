"""Storage helpers for uploaded media (news videos).

Uploaded files are written to ``settings.uploads_dir`` under a random name and
served back as static files mounted at ``/uploads``. The browser receives an
absolute URL (built from the request base URL) so the frontend can render the
media directly from the backend origin.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings

logger = logging.getLogger("kassem.media")

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v", ".ogv"}
CHUNK_SIZE = 1024 * 1024  # 1 MiB — keeps memory flat for large files


def uploads_root() -> Path:
    """Absolute path of the uploads directory, created on demand."""
    root = Path(settings.uploads_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _stored_name(filename: str) -> str:
    return Path(filename).name


def _public_url(base_url: str, filename: str) -> str:
    return f"{base_url.rstrip('/')}/uploads/{filename}"


async def save_video(file: UploadFile, base_url: str) -> dict:
    """Validate and persist an uploaded video, returning its public URL.

    Raises ``HTTPException`` on an unsupported extension, an empty file, or a
    file larger than ``settings.max_video_mb`` (partially written files are
    removed).
    """
    suffix = Path((file.filename or "").strip()).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة (mp4، webm، mov)")

    max_bytes = settings.max_video_mb * 1024 * 1024
    filename = f"{uuid.uuid4().hex}{suffix}"
    dest = uploads_root() / filename
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"حجم الفيديو يتجاوز {settings.max_video_mb} ميغابايت",
                    )
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    if size == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="الملف فارغ")

    logger.info("uploaded video %s (%.2f MB)", filename, size / 1024 / 1024)
    return {"url": _public_url(base_url, filename), "filename": filename, "size_bytes": size}


def delete_video(url_or_name: str | None) -> None:
    """Best-effort removal of a stored video; accepts a full URL or a file name."""
    if not url_or_name:
        return
    name = _stored_name(url_or_name.split("?")[0])
    if not name or Path(name).suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
        return
    target = uploads_root() / name
    if target.is_file():
        target.unlink(missing_ok=True)
        logger.info("deleted video %s", name)
