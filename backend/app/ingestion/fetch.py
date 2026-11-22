"""RSS/API fetching and normalization into a common `FetchedItem` shape."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import feedparser
import httpx
from dateutil import parser as date_parser

from app.config import settings
from app.ingestion import normalize as norm

logger = logging.getLogger("kassem.ingest.fetch")


@dataclass
class FetchedItem:
    title: str
    url: str
    summary: str = ""
    author: str = ""
    image_url: str | None = None
    published_at: datetime | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class FetchResult:
    ok: bool
    items: list[FetchedItem]
    error: str = ""
    http_status: int | None = None
    retries: int = 0


def _parse_date(entry) -> datetime | None:
    for key in ("published", "updated", "created"):
        value = entry.get(key) if isinstance(entry, dict) else getattr(entry, key, None)
        if value:
            try:
                dt = date_parser.parse(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except (ValueError, TypeError, OverflowError):
                continue
    parsed = entry.get("published_parsed") if isinstance(entry, dict) else None
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc)
    return None


def _extract_image(entry) -> str | None:
    # media:content / media:thumbnail
    for key in ("media_content", "media_thumbnail"):
        media = entry.get(key) if isinstance(entry, dict) else None
        if media:
            first = media[0]
            url = first.get("url")
            if url:
                return url
    # enclosure
    for enc in entry.get("enclosures", []) or []:
        if str(enc.get("type", "")).startswith("image"):
            return enc.get("href") or enc.get("url")
    # <img> inside summary/content
    for key in ("summary", "content"):
        value = entry.get(key)
        if not value:
            continue
        if isinstance(value, list):
            value = value[0].get("value", "")
        from app.ingestion.normalize import _TAGS  # noqa: PLC0415

        for chunk in _TAGS.split(str(value)):
            if "src=" in chunk and ("jpg" in chunk or "jpeg" in chunk or "png" in chunk or "webp" in chunk):
                import re  # noqa: PLC0415

                match = re.search(r'src=["\']([^"\']+)["\']', chunk)
                if match:
                    return match.group(1)
    return None


def _extract_author(entry) -> str:
    if entry.get("author"):
        return str(entry["author"])[:300]
    if entry.get("source") and isinstance(entry["source"], dict):
        return str(entry["source"].get("title", ""))[:300]
    return ""


def _normalize_entry(entry) -> FetchedItem | None:
    title = norm.strip_html(entry.get("title"))
    link = entry.get("link") or (entry.get("links") or [{}])[0].get("href")
    if not title or not link:
        return None
    summary = norm.strip_html(
        entry.get("summary") or (entry.get("description") if isinstance(entry, dict) else "") or ""
    )
    tags = [str(t.get("term", "")) for t in (entry.get("tags") or []) if t.get("term")]
    return FetchedItem(
        title=title[:500],
        url=link,
        summary=norm.truncate(summary, 1000),
        author=_extract_author(entry),
        image_url=_extract_image(entry),
        published_at=_parse_date(entry),
        tags=tags,
    )


def fetch_feed(feed_url: str, max_retries: int | None = None) -> FetchResult:
    """Fetch and parse an RSS/Atom feed with exponential-backoff retries."""
    retries_allowed = settings.ingestion_max_retries if max_retries is None else max_retries
    headers = {"User-Agent": settings.ingestion_user_agent, "Accept": "application/rss+xml, application/xml, text/xml, */*"}
    last_error = ""
    for attempt in range(retries_allowed + 1):
        try:
            with httpx.Client(timeout=settings.ingestion_timeout_seconds, follow_redirects=True) as client:
                response = client.get(feed_url, headers=headers)
            if response.status_code >= 400:
                last_error = f"HTTP {response.status_code}"
                if response.status_code in (429, 500, 502, 503, 504) and attempt < retries_allowed:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return FetchResult(ok=False, items=[], error=last_error, http_status=response.status_code, retries=attempt)
            parsed = feedparser.parse(response.content)
            if parsed.bozo and not parsed.entries:
                last_error = f"تعذر تحليل الخلاصة: {parsed.get('bozo_exception', 'unknown')}"
                if attempt < retries_allowed:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return FetchResult(ok=False, items=[], error=last_error, http_status=response.status_code, retries=attempt)
            items = [item for item in (_normalize_entry(e) for e in parsed.entries[:80]) if item]
            return FetchResult(ok=True, items=items, http_status=response.status_code, retries=attempt)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < retries_allowed:
                time.sleep(min(2 ** attempt, 8))
                continue
        except Exception as exc:  # defensive: never let one feed kill the run
            last_error = f"{type(exc).__name__}: {exc}"
            break
    return FetchResult(ok=False, items=[], error=last_error or "فشل غير معروف", retries=retries_allowed)
