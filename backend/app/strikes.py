"""Live strike/raid feed for the «الغارات» section.

Data is pulled from the ajwa2.com public API (Lebanon field reports: airstrikes,
shelling, drones, ground events). Results are cached briefly in-process so a busy
page never exceeds the upstream rate limit (120 req/min per IP).
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("kassem.strikes")

AJWA2_REPORTS_URL = "https://ajwa2.com/api/v1/reports"
CACHE_TTL_SECONDS = 60

# ajwa2 `type` code -> (Arabic label, category bucket)
_TYPE_CATALOG: dict[str, tuple[str, str]] = {
    "uav": ("مسيّرة استطلاع", "طيران"),
    "drone": ("درون", "طيران"),
    "fighter": ("طيران حربي", "طيران"),
    "helicopter": ("طيران مروحي", "طيران"),
    "tank": ("دبابة ميركافا", "ميداني"),
    "raid_fighter": ("غارة جوية حربية", "اعتداء"),
    "raid_drone": ("غارة - مسيّرة", "اعتداء"),
    "raid_helicopter": ("غارة - مروحي", "اعتداء"),
    "tank_shelling": ("قصف دبابة ميركافا", "اعتداء"),
    "bomb_drone": ("قنبلة مسيّرة", "اعتداء"),
    "bomb_quad": ("قنبلة من درون", "اعتداء"),
    "artillery": ("قصف مدفعي", "اعتداء"),
    "sweeping": ("تمشيط بالأسلحة", "اعتداء"),
    "explosion": ("تفجير", "اعتداء"),
    "infiltration": ("تسلل مشاة", "اعتداء"),
    "infantry": ("تسلل مدرّع", "اعتداء"),
    "flares": ("قنابل مضيئة", "اعتداء"),
    "shelling": ("قصف عام", "اعتداء"),
}

# Natural phenomena reported by ajwa2, out of scope for a strikes section.
_EXCLUDED_TYPES = {"lightning", "earthquake"}

# Upstream descriptions may carry an inline "(المصدر: ...)" note; the feed is
# presented under the platform's own attribution, so drop it.
_SOURCE_RE = re.compile(r"\s*[\(\[]المصدر:[^\)\]]*[\)\]]\s*")

_cache: dict[str, Any] = {"at": 0.0, "items": []}


def type_label(code: str) -> str:
    return _TYPE_CATALOG.get(code, ("حدث ميداني", "ميداني"))[0]


def type_category(code: str) -> str:
    return _TYPE_CATALOG.get(code, ("حدث ميداني", "ميداني"))[1]


def _clean_description(text: str) -> str:
    if not text:
        return ""
    text = _SOURCE_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize(report: dict) -> dict | None:
    code = str(report.get("type") or "").strip()
    if not code or code in _EXCLUDED_TYPES:
        return None
    return {
        "id": str(report.get("id") or ""),
        "short_code": str(report.get("short_code") or ""),
        "type": code,
        "type_label": type_label(code),
        "category": type_category(code),
        "city_name": str(report.get("city_name") or "").strip(),
        "description": _clean_description(report.get("description") or ""),
        "lat": report.get("lat"),
        "lon": report.get("lon"),
        "created_at": str(report.get("created_at") or ""),
        "approximate_location": bool(report.get("approximate_location", True)),
        "location_precision_m": report.get("location_precision_m"),
        "evidence_label": str(report.get("evidence_label") or ""),
    }


def _fetch_remote() -> list[dict]:
    headers = {
        "User-Agent": settings.ingestion_user_agent,
        "Accept": "application/json",
    }
    with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
        resp = client.get(AJWA2_REPORTS_URL, params={"window": "24h"})
        resp.raise_for_status()
        payload = resp.json()

    items: list[dict] = []
    for raw in payload.get("data", []) or []:
        normalized = _normalize(raw)
        if normalized:
            items.append(normalized)
    items.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return items


def fetch_reports() -> tuple[list[dict], float]:
    """Return ``(reports, cached_at_epoch)``.

    Served from an in-process cache for ``CACHE_TTL_SECONDS``. If the upstream
    call fails, the last good payload (possibly empty) is returned so the page
    degrades gracefully instead of erroring.
    """
    now = time.time()
    if _cache["items"] and now - _cache["at"] < CACHE_TTL_SECONDS:
        return _cache["items"], _cache["at"]
    try:
        items = _fetch_remote()
    except Exception as exc:  # noqa: BLE001 - degrade gracefully on upstream errors
        logger.warning("ajwa2 strikes fetch failed: %s", exc)
        return _cache["items"], _cache["at"]
    _cache["items"] = items
    _cache["at"] = now
    return items, now
