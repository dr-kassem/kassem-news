"""Tests for uploaded news-video storage (app.media)."""
from __future__ import annotations

import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app import media
from app.config import settings


def _upload(data: bytes, filename: str) -> UploadFile:
    return UploadFile(file=BytesIO(data), filename=filename)


@pytest.fixture()
def uploads_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    return tmp_path


def test_save_video_writes_file_and_returns_url(uploads_tmp):
    info = asyncio.run(media.save_video(_upload(b"fake-mp4-bytes", "clip.mp4"), "http://127.0.0.1:8000"))

    name = info["filename"]
    assert name.endswith(".mp4")
    assert info["url"] == f"http://127.0.0.1:8000/uploads/{name}"
    assert info["size_bytes"] == len(b"fake-mp4-bytes")
    assert (uploads_tmp / name).read_bytes() == b"fake-mp4-bytes"


def test_save_video_rejects_bad_extension(uploads_tmp):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(media.save_video(_upload(b"data", "malware.exe"), "http://x"))
    assert exc.value.status_code == 400
    assert list(uploads_tmp.iterdir()) == []


def test_save_video_rejects_empty_file(uploads_tmp):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(media.save_video(_upload(b"", "clip.mp4"), "http://x"))
    assert exc.value.status_code == 400
    assert list(uploads_tmp.iterdir()) == []


def test_save_video_enforces_max_size(uploads_tmp, monkeypatch):
    monkeypatch.setattr(settings, "max_video_mb", 0)  # any byte exceeds the limit
    with pytest.raises(HTTPException) as exc:
        asyncio.run(media.save_video(_upload(b"x" * 10, "clip.mp4"), "http://x"))
    assert exc.value.status_code == 413
    # No partially written file is left behind.
    assert list(uploads_tmp.iterdir()) == []


def test_delete_video_removes_file_and_ignores_traversal(uploads_tmp):
    info = asyncio.run(media.save_video(_upload(b"data", "clip.webm"), "http://x"))
    target = uploads_tmp / info["filename"]
    assert target.exists()

    media.delete_video(info["url"])
    assert not target.exists()

    # A traversal attempt must never touch files outside the uploads dir.
    outside = uploads_tmp.parent / "secret.mp4"
    outside.write_bytes(b"keep")
    media.delete_video("../secret.mp4")
    assert outside.exists()
