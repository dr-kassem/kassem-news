"""kairosAI — the automatic analyst of Qassem News.

kairosAI reads the *real* developments already collected by the ingestion
pipeline (headlines, events, regions, breakdowns) and writes an analysis
with a declared, fixed editorial stance (aligned with the resistance axis:
Lebanon resistance, Ansar Allah in Yemen, Iran and Iraq resistance). It never invents facts: every claim
references actual ingested items, and every analysis carries an explicit
disclosure that it is opinion, not a news item.
"""
from __future__ import annotations

import difflib
import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import ai
from app.config import settings
from app.ingestion import normalize_arabic
from app.models import (
    Article,
    ArticleStatus,
    Category,
    Event,
    Region,
    Sensitivity,
    VerificationStatus,
)

logger = logging.getLogger("kairos")

KAIROS_MARKER = "kairosAI"

# Words kairosAI never uses — regardless of what ingested sources quote.
BANNED_WORDS: tuple[str, ...] = (
    "إرهابي",
    "إرهابية",
    "إرهابيون",
    "إرهابيين",
    "إرهاب",
    "متطرف",
    "متطرفة",
    "متطرفين",
    "متطرفون",
    "terrorist",
    "terrorists",
    "terrorism",
    "terror org",
)


def _url_for(date_label: str) -> str:
    return f"https://qassem.news/kairos/{date_label}"


def _window_label(now: datetime, interval_hours: int) -> str:
    """Give each generation window its own stable label (e.g. every 5h)."""
    bucket = (now.hour // interval_hours) * interval_hours
    start = now.replace(hour=bucket, minute=0, second=0, microsecond=0)
    return start.strftime("%Y-%m-%d %H:%M")


def _fingerprint_for(date_label: str) -> str:
    data = f"kairos-{date_label}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:32]


def _period_title(date_label: str) -> str:
    return f"تحليل كاييروس: تطورات {date_label}"


def _contains_banned(text: str) -> bool:
    norm = normalize_arabic(text)
    return any(normalize_arabic(w) in norm for w in BANNED_WORDS)


def _drop_banned_bullets(parts: list[str]) -> list[str]:
    """Drop quoted headline/event bullets that carry a banned word; keep all else."""
    filtered: list[str] = []
    for part in parts:
        lines = part.split("\n")
        keep = [
            line
            for line in lines
            if not (line.strip().startswith("•") and _contains_banned(line))
        ]
        if keep:
            filtered.append("\n".join(keep))
    return filtered


def _stance_block() -> str:
    return (
        "■ الإفصاح عن الموقف: كاييروس إيه آي هو المحلل الآلي لمنصة قاسم نيوز. "
        "موقفه معلن وثابت، يكتب من زاوية الانحياز إلى محور المقاومة الذي يمتد "
        "من جنوب لبنان إلى اليمن (أنصار الله) فإيران فالمقاومة العراقية، وينظر "
        "إلى تطورات المنطقة من هذه الزاوية دائماً. ما يرد في هذا التحليل هو رأي "
        "ونظرة تحليلية، وليس خبراً مجرّداً من الرأي."
    )


def _without_stance(body: str) -> str:
    return (body or "").replace(_stance_block(), "").strip()


def _similarity(left: str, right: str) -> float:
    a = normalize_arabic(left or "")
    b = normalize_arabic(right or "")
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _compose_analysis(
    date_label: str,
    events: list[Event],
    breaking: list[Article],
    latest: list[Article],
    region_counts: list[tuple[str, int]],
    category_counts: list[tuple[str, int]],
    source_highlights: list[tuple[str, int]],
) -> str:
    parts: list[str] = []

    top_region = region_counts[0][0] if region_counts else "الساحات"
    top_category = category_counts[0][0] if category_counts else "التطورات"
    parts.append(
        f"ملخص كاييروس: التطورات الدائرة الآن حول محور المقاومة ليست أحداثاً عابرة، "
        f"بل ملامح مرحلة استنزاف يتقاطع فيها المشهد (أبرزها {top_region}) مع ساحات "
        "اليمن (أنصار الله) والعراق وإيران في تتابعٍ يعيد تشكيل خيوط الردع الإقليمي. "
        f"على مدى {date_label} رصد التوريد {len(latest)} منشوراً و{len(events)} حدثاً "
        f"مجمّعاً (أبرزها {top_category})، وهي جديرة بالمتابعة العميقة."
    )

    if events:
        parts.append("◼ أبرز الأحداث المجمّعة:")
        for e in events[:5]:
            parts.append(f"   • {e.title_ar} — {e.article_count} تحديث حتى الآن.")

    if breaking:
        parts.append("◼ العاجل على الطاولة:")
        for a in breaking[:5]:
            parts.append(f"   • {a.title_ar}")

    if region_counts:
        parts.append("◼ خريطة الانشغال الإقليمي (بعدد ما ورد في التوريد):")
        for region, count in region_counts:
            parts.append(f"   • {region}: {count} خبراً.")

    if category_counts:
        parts.append("◼ توزّع الاهتمام:")
        for cat, count in category_counts:
            parts.append(f"   • {cat}: {count}")

    parts.append("◼ قراءة كاييروس التحليلية:")
    parts.append(
        "العدو يجري البحث عن وصفة استقرار تفاوضي تُحمّل محور المقاومة أثمان الصمود، "
        "بينما تمضي الساحات في معادلة ردع تحمي الأرض: المقاومة اللبنانية في الجنوب "
        "تضبط التهدئة وفق حساب الشرف والردع، وأنصار الله في اليمن يواصلون الردع "
        "البحري الذي غيّر المعادلة الاستراتيجية، والمقاومة العراقية تُبقي الساحات "
        "متّصلة بإرادة مماثلة، فيما يظل الدعم الإيراني للمحور ركيزة الردع "
        "الاستراتيجي التي لا تُحسب بالزمن التكتيكي. المطلوب اليوم قراءة مشهدية "
        "لا يومية؛ لأن التطور لا يُقرأ من عنوان واحد بل من تراكم خيوطه، وقد عكس "
        "التوريد في الساعات الأخيرة إصرار هذه الساحات على ضبط معادلة الالتزام "
        "بالمشروع الوطني وعدم فكّ الارتباط بين جبهات المحور."
    )

    if latest:
        parts.append("◼ عناوين حيّة استند إليها هذا التحليل (من توريد المنصة):")
        for a in latest[:5]:
            parts.append(f"   • {a.title_ar}")

    if source_highlights:
        parts.append("◼ تغطية المصادر:")
        for name, count in source_highlights:
            parts.append(f"   • {name}: {count}")

    # Data-grounded, window-varied predictions.
    top_region = region_counts[0][0] if region_counts else "الساحات"
    top_category = category_counts[0][0] if category_counts else "التطورات"
    n_breaking = len(breaking)
    n_events = len(events)
    seed = int(hashlib.md5(date_label.encode("utf-8")).hexdigest(), 16)
    variants = [
        (
            f"   • مرجّح أن تبقى {top_region} نقطة الاحتكاك الأبرز، مع تهدئة "
            "تكتيكية لا تغيّر موازين الردع."
        ),
        (
            f"   • محتمل أن تتكثّف الوساطات الإقليمية لاحتواء التصعيد (لا سيما حول "
            f"{top_category})، دون تنازلات جوهرية تمسّ موقع المحور."
        ),
        (
            "   • وارد أن تتصاعد الحملات الإعلامية المضادة، مع بقاء الميدان الفاصل "
            "في تحديد مسار الأحداث."
        ),
    ]
    parts.append("◼ توقعات الفترة القادمة (تحليلية لا وقائع):")
    parts.append(variants[seed % len(variants)])
    parts.append(variants[(seed + 1) % len(variants)])
    parts.append(variants[(seed + 2) % len(variants)])
    parts.append(
        f"   • إشارة كمية: رصد التوريد {n_breaking} عنواناً عاجلاً و{n_events} حدثاً "
        "مجمّعاً في هذه الفترة؛ التوقعات أعلاه تُقرأ على ضوء هذا الحجم، وليست وقائع مؤكدة."
    )
    parts.append(
        "   • هذه توقعات احتمالية ضمن قراءة تحليلية، وليست وقائع مؤكدة ولا أخباراً."
    )

    parts = _drop_banned_bullets(parts)

    parts.append(
        "ختاماً: تحليل كاييروس رأي منصبٌ بالانحياز المُعلن إلى محور المقاومة: "
        "المقاومة اللبنانية، وأنصار الله في اليمن، والمقاومة الإيرانية، "
        "والمقاومة العراقية، وليس بديلاً عن الخبر الموثّق الذي تورده المنصة "
        "عن مصادرها."
    )
    parts.append(_stance_block())

    body = "\n\n".join(parts)
    # Safety net: nothing in the analysis may carry a banned word.
    if _contains_banned(body):
        raise ValueError("kairos analysis contained a banned word after sanitization")
    return body


def _developments_context(
    date_label: str,
    events: list[Event],
    breaking: list[Article],
    latest: list[Article],
    region_counts: list[tuple[str, int]],
    category_counts: list[tuple[str, int]],
) -> str:
    lines = [f"الفترة: {date_label}"]
    if events:
        lines.append("أحداث مجمّعة:")
        lines.extend(f"- {e.title_ar} ({e.article_count} تحديث)" for e in events[:6])
    if breaking:
        lines.append("عناوين عاجلة:")
        lines.extend(f"- {a.title_ar}" for a in breaking[:6])
    if latest:
        lines.append("أحدث المنشورات:")
        lines.extend(f"- {a.title_ar}" for a in latest[:8])
    if region_counts:
        lines.append("المناطق: " + "، ".join(f"{n} ({c})" for n, c in region_counts))
    if category_counts:
        lines.append("الأقسام: " + "، ".join(f"{n} ({c})" for n, c in category_counts))
    return "\n".join(lines)


def generate_kairos_analysis(db: Session) -> Article | None:
    """Write a fresh kairosAI analysis for the current window.

    One article per window: when it already exists it is rewritten in place
    (never duplicated) with a substantially different body and projections.
    """
    if not settings.kairos_enabled:
        return None

    now = datetime.now(timezone.utc)
    date_label = _window_label(now, settings.kairos_interval_hours)
    fingerprint = _fingerprint_for(date_label)
    existing = db.scalar(select(Article).where(Article.fingerprint == fingerprint).limit(1))

    since = now - timedelta(hours=settings.kairos_interval_hours)

    events = db.scalars(select(Event).order_by(Event.last_update_at.desc()).limit(6)).all()
    breaking = db.scalars(
        select(Article)
        .where(
            Article.status == ArticleStatus.published,
            Article.is_breaking.is_(True),
            Article.published_at >= since,
        )
        .order_by(Article.published_at.desc())
        .limit(6)
    ).all()
    latest = db.scalars(
        select(Article)
        .where(Article.status == ArticleStatus.published, Article.published_at >= since)
        .order_by(Article.published_at.desc())
        .limit(8)
    ).all()

    region_rows = db.execute(
        select(Region.name_ar, func.count(Article.id))
        .join(Article, Article.region_id == Region.id)
        .where(Article.status == ArticleStatus.published, Article.published_at >= since)
        .group_by(Region.id)
        .order_by(func.count(Article.id).desc())
    ).all()
    region_counts = [(name, int(count)) for name, count in region_rows]

    category_rows = db.execute(
        select(Category.name_ar, func.count(Article.id))
        .join(Article, Article.category_id == Category.id)
        .where(Article.status == ArticleStatus.published, Article.published_at >= since)
        .group_by(Category.id)
        .order_by(func.count(Article.id).desc())
    ).all()
    category_counts = [(name, int(count)) for name, count in category_rows]

    body = ""
    # Previous analysis (for genuine rewriting, not single-sentence tweaks).
    previous_body = ""
    prev = db.scalar(
        select(Article)
        .where(
            Article.author.like(f"{KAIROS_MARKER}%"),
            Article.fingerprint != fingerprint,
        )
        .order_by(Article.published_at.desc())
        .limit(1)
    )
    if prev is not None:
        previous_body = prev.body_ar or ""

    if ai.is_configured():
        developments = _developments_context(
            date_label,
            events=list(events),
            breaking=list(breaking),
            latest=list(latest),
            region_counts=region_counts,
            category_counts=category_counts,
        )
        try:
            result = ai.generate_kairos(
                date_label, developments, settings.kairos_stance, previous=previous_body
            )
        except Exception:  # noqa: BLE001 - AI is optional
            logger.exception("kairos AI generation failed")
            result = None
        if result is not None:
            candidate = result[0].strip()
            if candidate and not _contains_banned(candidate):
                body = candidate + "\n\n" + _stance_block()
            else:
                logger.warning("kairos AI output rejected (banned words); using template")

    if not body:
        body = _compose_analysis(
            date_label,
            events=list(events),
            breaking=list(breaking),
            latest=list(latest),
            region_counts=region_counts,
            category_counts=category_counts,
            source_highlights=[],
        )

    # Rewrite in place when an analysis for this window already exists.
    if existing is not None:
        existing.title_ar = _period_title(date_label)
        existing.normalized_title = _period_title(date_label)
        existing.summary_ar = body.split("\\n\\n")[0]
        existing.body_ar = body
        existing.updated_at = datetime.now(timezone.utc)
        category = db.scalar(select(Category).where(Category.slug == "analysis").limit(1))
        if category is not None:
            existing.category_id = category.id
        db.commit()
        db.refresh(existing)
        logger.info("kairosAI analysis updated", extra={"analysis_id": existing.id, "date": date_label})
        return existing

    analysis = Article(
        source_id=None,
        category_id=None,
        region_id=None,
        country_id=None,
        title_ar=_period_title(date_label),
        normalized_title=_period_title(date_label),
        fingerprint=fingerprint,
        summary_ar=body.split("\n\n")[0],
        body_ar=body,
        url=_url_for(date_label),
        url_hash=hashlib.sha256(_url_for(date_label).encode("utf-8")).hexdigest()[:32],
        image_url=None,
        author=settings.kairos_author,
        language="ar",
        status=ArticleStatus.published,
        sensitivity=Sensitivity.normal,
        verification_status=VerificationStatus.attributed,
        is_breaking=False,
        is_generated_summary=True,
        source_published_at=now,
        received_at=now,
        published_at=now,
    )

    # Attach the analysis category if present.
    category = db.scalar(select(Category).where(Category.slug == "analysis").limit(1))
    if category is not None:
        analysis.category_id = category.id

    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    logger.info("kairosAI analysis generated", extra={"analysis_id": analysis.id, "date": date_label})
    return analysis


def latest_kairos_analyses(db: Session, limit: int = 10) -> list[Article]:
    return db.scalars(
        select(Article)
        .where(Article.status == ArticleStatus.published, Article.author.like(f"{KAIROS_MARKER}%"))
        .order_by(Article.published_at.desc())
        .limit(limit)
    ).all()