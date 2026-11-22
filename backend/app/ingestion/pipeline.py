"""Ingestion orchestration: fetch -> normalize -> dedupe -> classify -> route."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import ai
from app.config import settings
from app.ingestion import fingerprint, normalize_arabic, truncate, url_hash
from app.ingestion import classify, dedupe
from app.ingestion.fetch import FetchedItem, fetch_feed
from app.models import (
    Article,
    ArticleStatus,
    Category,
    Country,
    Duplicate,
    Event,
    EventArticle,
    IngestionError,
    IngestionRun,
    PublishAction,
    PublicationLog,
    Region,
    RunStatus,
    Sensitivity,
    Source,
    VerificationStatus,
)
from app.publishing import evaluate, get_rules

logger = logging.getLogger("kassem.ingest.pipeline")

CANDIDATE_WINDOW_DAYS = 5
CANDIDATE_LIMIT = 400


@dataclass
class SourceOutcome:
    fetched: int = 0
    new: int = 0
    published: int = 0
    review: int = 0
    duplicates: int = 0
    filtered: int = 0
    error: str = ""

def _blocked_keywords() -> list[str]:
    return [k.strip() for k in (settings.ingestion_blocked_keywords or "").split(",") if k.strip()]

def _is_blocked(text: str) -> bool:
    if not text:
        return False
    norm = normalize_arabic(text)
    for kw in _blocked_keywords():
        if normalize_arabic(kw) and normalize_arabic(kw) in norm:
            return True
    return False


def _taxonomy_maps(db: Session):
    categories = {c.slug: c.id for c in db.scalars(select(Category)).all()}
    regions = {r.slug: r.id for r in db.scalars(select(Region)).all()}
    countries = {c.iso_code: c.id for c in db.scalars(select(Country)).all()}
    return categories, regions, countries


def _compose_body(item: FetchedItem, source: Source | None) -> str:
    return item.summary or ""


def _looks_arabic(text: str) -> bool:
    if not text:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    arabic = sum(1 for c in letters if "\u0600" <= c <= "\u06FF")
    return arabic / len(letters) >= 0.4


def _ai_enrich(
    item: FetchedItem, source: Source | None, ai_budget: dict | None
) -> dict[str, str] | None:
    if ai_budget is None or ai_budget.get("remaining", 0) <= 0:
        return None
    if not (settings.ai_summarize_on_ingest and ai.is_configured()):
        return None
    if _looks_arabic(f"{item.title} {item.summary or ''}"):
        return None
    enriched = ai.translate_and_summarize(
        item.title, item.summary or "", source.name_ar if source else ""
    )
    if enriched is not None:
        ai_budget["remaining"] = ai_budget.get("remaining", 1) - 1
    return enriched


def _recent_candidates(db: Session) -> list[Article]:
    since = datetime.now(timezone.utc) - timedelta(days=CANDIDATE_WINDOW_DAYS)
    stmt = (
        select(Article)
        .where(or_(Article.received_at >= since, Article.source_published_at >= since))
        .order_by(Article.received_at.desc())
        .limit(CANDIDATE_LIMIT)
    )
    return list(db.scalars(stmt).all())


def _attach_event(db: Session, article: Article, candidates: list[Article],
                  threshold: float) -> None:
    for candidate in candidates:
        if candidate.event_id is None:
            continue
        if dedupe.similarity(article.normalized_title, candidate.normalized_title) >= threshold:
            event = db.get(Event, candidate.event_id)
            if event is not None:
                article.event_id = event.id
                event.article_count = (event.article_count or 0) + 1
                event.last_update_at = datetime.now(timezone.utc)
                db.add(EventArticle(event_id=event.id, article_id=article.id,
                                    similarity=dedupe.similarity(article.normalized_title, candidate.normalized_title)))
                return
    event = Event(
        title_ar=article.title_ar,
        summary_ar=truncate(article.summary_ar or article.title_ar, 400),
        is_developing=article.verification_status == VerificationStatus.developing,
        article_count=1,
    )
    db.add(event)
    db.flush()
    article.event_id = event.id
    db.add(EventArticle(event_id=event.id, article_id=article.id, similarity=1.0))


def _store_item(db: Session, source: Source | None, item: FetchedItem, rules: dict,
                candidates: list[Article], categories, regions, countries,
                ai_budget: dict | None = None) -> tuple[str, Article | None]:
    """Return one of: 'duplicate' | 'new'. Mutates candidates list."""
    u_hash = url_hash(item.url)
    if db.scalar(select(Article.id).where(Article.url_hash == u_hash)):
        return "duplicate", None

    normalized = fingerprint(item.title)
    existing = db.scalar(
        select(Article).where(Article.fingerprint == normalized).limit(1)
    )
    dup_match, dup_score = None, 0.0
    if existing is None:
        dup_match, dup_score = dedupe.best_match(
            item.title, candidates, rules["duplicate_threshold"]
        )
    if existing is not None or dup_match is not None:
        target = existing or dup_match
        db.add(Duplicate(article_id=None, duplicate_of_id=target.id, url=item.url,
                         similarity=1.0 if existing else dup_score))
        return "duplicate", None

    enriched = _ai_enrich(item, source, ai_budget)
    title_ar = enriched["title_ar"] if enriched else item.title
    summary_ar = enriched["summary_ar"] if enriched else (item.summary or item.title)
    body_text = enriched["summary_ar"] if enriched else _compose_body(item, source)

    category_slug = classify.detect_category(title_ar, summary_ar)
    region_slug = classify.detect_region(title_ar, summary_ar)
    country_iso = classify.detect_country(title_ar, summary_ar)

    decision = evaluate(
        source,
        rules,
        title=title_ar,
        body=summary_ar,
        has_image=bool(item.image_url),
        category_slug=category_slug or "world",
        published_at=item.published_at,
    )

    now = datetime.now(timezone.utc)
    article = Article(
        source_id=source.id if source else None,
        category_id=categories.get(category_slug) if category_slug else None,
        region_id=regions.get(region_slug) if region_slug else None,
        country_id=countries.get(country_iso) if country_iso else None,
        title_ar=title_ar,
        normalized_title=title_ar,
        fingerprint=normalized,
        summary_ar=truncate(summary_ar, 320),
        body_ar=body_text,
        url=item.url,
        url_hash=u_hash,
        image_url=item.image_url,
        author=item.author,
        status=decision.status,
        sensitivity=(
            Sensitivity.sensitive if decision.is_sensitive else Sensitivity.normal
        ),
        verification_status=decision.verification_status,
        is_breaking=decision.is_breaking,
        is_strike=classify.is_strike(item.title, item.summary),
        is_generated_summary=True,
        source_published_at=item.published_at,
        received_at=now,
        published_at=now if decision.status == ArticleStatus.published else None,
    )
    db.add(article)
    db.flush()

    _attach_event(db, article, candidates, rules["event_threshold"])

    note = " | ".join(decision.reasons) or "استيراد تلقائي"
    db.add(PublicationLog(article_id=article.id, action=PublishAction.created, note=note))
    if decision.status == ArticleStatus.published:
        db.add(PublicationLog(article_id=article.id, action=PublishAction.published, note="نشر تلقائي"))

    candidates.append(article)
    return "new", article


def ingest_source(db: Session, source: Source, rules: dict, run: IngestionRun,
                  categories, regions, countries,
                  ai_budget: dict | None = None) -> SourceOutcome:
    outcome = SourceOutcome()
    result = fetch_feed(source.feed_url)
    source.last_fetched_at = datetime.now(timezone.utc)
    if not result.ok:
        outcome.error = result.error
        source.last_status = f"خطأ: {result.error}"[:200]
        db.add(IngestionError(run_id=run.id, source_id=source.id,
                              message=result.error, retry_count=result.retries))
        logger.warning("feed failed", extra={"source_id": source.id})
        db.commit()
        return outcome

    outcome.fetched = len(result.items)
    candidates = _recent_candidates(db)
    for item in result.items:
        if _is_blocked(f"{item.title} {item.summary or ''}"):
            outcome.filtered += 1
            logger.info("item filtered (blocked keyword)", extra={"source_id": source.id, "url": item.url})
            continue
        try:
            kind, article = _store_item(db, source, item, rules, candidates,
                                        categories, regions, countries, ai_budget)
        except Exception as exc:  # noqa: BLE001 - isolate per-item failures
            db.rollback()
            db.add(IngestionError(run_id=run.id, source_id=source.id,
                                  message=f"{item.url}: {type(exc).__name__}: {exc}"))
            logger.exception("item failed", extra={"source_id": source.id})
            continue
        if kind == "duplicate":
            outcome.duplicates += 1
        elif article is not None:
            outcome.new += 1
            if article.status == ArticleStatus.published:
                outcome.published += 1
            elif article.status == ArticleStatus.review:
                outcome.review += 1

    source.last_status = f"نجاح: {outcome.new} جديد"
    db.commit()
    return outcome


def run_ingestion(db: Session, trigger: str = "scheduled",
                  source_ids: list[int] | None = None) -> IngestionRun:
    run = IngestionRun(trigger=trigger, status=RunStatus.running)
    db.add(run)
    db.commit()
    db.refresh(run)

    rules = get_rules(db)
    query = select(Source).where(Source.is_active.is_(True))
    if source_ids:
        query = query.where(Source.id.in_(source_ids))
    sources = list(db.scalars(query).all())

    run.sources_total = len(sources)
    db.commit()

    categories, regions, countries = _taxonomy_maps(db)
    ai_budget = (
        {"remaining": settings.ai_ingest_max_per_run}
        if settings.ai_summarize_on_ingest
        else None
    )

    for source in sources:
        try:
            outcome = ingest_source(
                db, source, rules, run, categories, regions, countries, ai_budget
            )
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            run.sources_failed += 1
            run.errors += 1
            run.notes = (run.notes + f"\n[{source.slug}] {exc}")[:2000]
            db.add(IngestionError(run_id=run.id, source_id=source.id,
                                  message=f"{type(exc).__name__}: {exc}"))
            db.commit()
            continue
        if outcome.error:
            run.sources_failed += 1
        else:
            run.sources_ok += 1
        run.articles_fetched += outcome.fetched
        run.articles_new += outcome.new
        run.articles_published += outcome.published
        run.articles_review += outcome.review
        run.duplicates += outcome.duplicates
        run.errors += 1 if outcome.error else 0
        db.commit()

    run.finished_at = datetime.now(timezone.utc)
    if run.sources_failed == 0:
        run.status = RunStatus.success
    elif run.sources_ok == 0:
        run.status = RunStatus.failed
    else:
        run.status = RunStatus.partial
    db.commit()
    db.refresh(run)
    logger.info("ingestion finished", extra={"run_id": run.id})
    return run
