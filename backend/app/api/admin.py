"""Administrative API: dashboard, moderation, sources, rules, ingestion, users."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app import ai, media
from app.api.helpers import _load_options, article_to_list_item
from app.config import settings
from app.database import get_db
from app.deps import Pagination, get_pagination, require_role
from app.ingestion import fingerprint, truncate, url_hash
from app.ingestion.fetch import fetch_feed
from app.ingestion.pipeline import run_ingestion
from app.models import (
    Article,
    ArticleStatus,
    Category,
    Correction,
    Country,
    Duplicate,
    EventArticle,
    IngestionError,
    IngestionRun,
    PublishAction,
    PublicationLog,
    PublishingRule,
    Region,
    Role,
    RunStatus,
    Sensitivity,
    Source,
    SourceType,
    User,
    VerificationStatus,
)
from app.publishing import DEFAULTS, ensure_default_rules, get_rules, set_rule
from app.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIEnrichResponse,
    AIStatus,
    ArticleCreateManual,
    ArticleListItem,
    ArticleUpdate,
    ArticleActionRequest,
    CategoryCreate,
    CategoryOut,
    CorrectionOut,
    CorrectionRequest,
    DashboardStats,
    IngestionErrorOut,
    IngestionRunOut,
    PublicationLogOut,
    RuleOut,
    RuleUpdate,
    SourceCreate,
    SourceOut,
    SourceTestResult,
    SourceUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

_reviewer = require_role(Role.reviewer)
_editor = require_role(Role.editor)
_admin = require_role(Role.admin)


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), _: User = Depends(_reviewer)) -> DashboardStats:
    def count(stmt):
        return db.scalar(stmt) or 0

    return DashboardStats(
        total_articles=count(select(func.count(Article.id))),
        published=count(select(func.count(Article.id)).where(Article.status == ArticleStatus.published)),
        pending_review=count(select(func.count(Article.id)).where(Article.status == ArticleStatus.review)),
        duplicates_detected=count(select(func.count(Duplicate.id))),
        failed_fetches=count(select(func.count(IngestionError.id))),
        active_sources=count(select(func.count(Source.id)).where(Source.is_active.is_(True))),
        total_sources=count(select(func.count(Source.id))),
        total_events=count(select(func.count(func.distinct(Article.event_id)))),
        last_run=db.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(1)).first(),
        recent_runs=list(db.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(5)).all()),
        recent_errors=list(db.scalars(select(IngestionError).order_by(IngestionError.created_at.desc()).limit(5)).all()),
    )


# --------------------------------------------------------------------------- #
# Articles moderation
# --------------------------------------------------------------------------- #
@router.get("/articles", response_model=dict)
def admin_articles(
    db: Session = Depends(get_db),
    _: User = Depends(_reviewer),
    pagination: Pagination = Depends(get_pagination),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    source_id: int | None = Query(default=None),
    category_id: int | None = Query(default=None),
):
    query = select(Article).options(*_load_options())
    count_query = select(func.count(Article.id))
    if status:
        query = query.where(Article.status == ArticleStatus(status))
        count_query = count_query.where(Article.status == ArticleStatus(status))
    if q:
        like = f"%{q.strip()}%"
        query = query.where(Article.title_ar.ilike(like))
        count_query = count_query.where(Article.title_ar.ilike(like))
    if source_id:
        query = query.where(Article.source_id == source_id)
        count_query = count_query.where(Article.source_id == source_id)
    if category_id:
        query = query.where(Article.category_id == category_id)
        count_query = count_query.where(Article.category_id == category_id)

    total = db.scalar(count_query) or 0
    rows = db.scalars(
        query.order_by(Article.received_at.desc()).offset(pagination.offset).limit(pagination.limit)
    ).all()
    return {
        "items": [article_to_list_item(a) for a in rows],
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total": total,
        "pages": max((total + pagination.page_size - 1) // pagination.page_size, 1),
    }


def _log(db: Session, article_id: int, action: PublishAction, actor: User | None, note: str = ""):
    db.add(PublicationLog(article_id=article_id, action=action,
                          actor_user_id=actor.id if actor else None, note=note))


@router.post("/articles", response_model=ArticleListItem, status_code=201)
def create_manual(payload: ArticleCreateManual, db: Session = Depends(get_db),
                  user: User = Depends(_editor)):
    raw_url = payload.url.strip()
    if not raw_url:
        raw_url = f"https://kassem.news/manual/{uuid.uuid4()}"
    now = datetime.now(timezone.utc)
    article = Article(
        source_id=None,
        category_id=payload.category_id,
        region_id=payload.region_id,
        country_id=payload.country_id,
        title_ar=payload.title_ar,
        normalized_title=payload.title_ar,
        fingerprint=fingerprint(payload.title_ar),
        summary_ar=payload.summary_ar,
        body_ar=payload.body_ar,
        url=raw_url,
        url_hash=url_hash(raw_url),
        image_url=payload.image_url,
        video_url=payload.video_url,
        author=payload.author or user.full_name,
        status=ArticleStatus.published if payload.publish_now else ArticleStatus.pending,
        sensitivity=payload.sensitivity,
        verification_status=payload.verification_status,
        is_breaking=payload.is_breaking,
        is_generated_summary=False,
        received_at=now,
        published_at=now if payload.publish_now else None,
    )
    db.add(article)
    db.flush()
    _log(db, article.id, PublishAction.created, user, "إنشاء يدوي")
    if payload.publish_now:
        _log(db, article.id, PublishAction.published, user)
    db.commit()
    db.refresh(article)
    return article_to_list_item(article)


@router.get("/articles/{article_id}", response_model=dict)
def get_article(article_id: int, db: Session = Depends(get_db),
                user: User = Depends(_editor)) -> dict:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    return {
        "id": article.id,
        "title_ar": article.title_ar,
        "summary_ar": article.summary_ar,
        "body_ar": article.body_ar,
        "image_url": article.image_url,
        "video_url": article.video_url,
        "category_id": article.category_id,
        "region_id": article.region_id,
        "is_breaking": article.is_breaking,
        "sensitivity": article.sensitivity.value,
        "verification_status": article.verification_status.value,
        "status": article.status.value,
    }


@router.patch("/articles/{article_id}", response_model=ArticleListItem)
def update_article(article_id: int, payload: ArticleUpdate,
                   db: Session = Depends(get_db), user: User = Depends(_editor)):
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    changed = payload.model_dump(exclude_unset=True)
    for field, value in changed.items():
        previous = getattr(article, field)
        if previous != value:
            db.add(Correction(article_id=article.id, user_id=user.id, field=field,
                              previous_value=str(previous or ""), new_value=str(value or ""),
                              reason="تعديل تحريري"))
            if field == "video_url":
                media.delete_video(previous)
            setattr(article, field, value)
    if "title_ar" in changed:
        article.normalized_title = article.title_ar
        article.fingerprint = fingerprint(article.title_ar)
    _log(db, article.id, PublishAction.updated, user, ",".join(changed.keys()))
    db.commit()
    db.refresh(article)
    return article_to_list_item(article)


@router.delete("/articles/{article_id}", status_code=204)
def delete_article(article_id: int, db: Session = Depends(get_db),
                   user: User = Depends(_editor)) -> Response:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    # Remove dependent rows explicitly so the delete works even when SQLite
    # foreign-key enforcement is off.
    db.query(Duplicate).filter(
        or_(Duplicate.article_id == article_id, Duplicate.duplicate_of_id == article_id)
    ).delete(synchronize_session=False)
    db.query(EventArticle).filter(EventArticle.article_id == article_id).delete(synchronize_session=False)
    db.query(Correction).filter(Correction.article_id == article_id).delete(synchronize_session=False)
    db.query(PublicationLog).filter(PublicationLog.article_id == article_id).delete(synchronize_session=False)
    media.delete_video(article.video_url)
    db.delete(article)
    db.commit()
    return Response(status_code=204)


# --------------------------------------------------------------------------- #
# Media uploads (news videos)
# --------------------------------------------------------------------------- #
@router.post("/uploads/videos", status_code=201)
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    _: User = Depends(_editor),
) -> dict:
    """Upload a video for a news item and return its absolute public URL."""
    return await media.save_video(file, str(request.base_url))


@router.delete("/uploads/videos/{filename}", status_code=204)
def delete_video(filename: str, _: User = Depends(_editor)) -> Response:
    media.delete_video(filename)
    return Response(status_code=204)


# --------------------------------------------------------------------------- #
# Duplicate (repeated) news log
# --------------------------------------------------------------------------- #
@router.get("/duplicates", response_model=list[dict])
def list_duplicates(
    limit: int = Query(300, ge=1, le=2000),
    db: Session = Depends(get_db),
    _: User = Depends(_reviewer),
) -> list[dict]:
    rows = db.execute(
        select(Duplicate, Article.title_ar, Article.url)
        .outerjoin(Article, Duplicate.duplicate_of_id == Article.id)
        .order_by(Duplicate.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": dup.id,
            "url": dup.url,
            "similarity": round(dup.similarity, 3),
            "created_at": dup.created_at,
            "duplicate_of_id": dup.duplicate_of_id,
            "duplicate_of_title": title or "",
            "duplicate_of_url": original_url or "",
        }
        for dup, title, original_url in rows
    ]


@router.delete("/duplicates/{duplicate_id}", status_code=204)
def delete_duplicate(duplicate_id: int, db: Session = Depends(get_db),
                     _: User = Depends(_editor)) -> Response:
    dup = db.get(Duplicate, duplicate_id)
    if dup is None:
        raise HTTPException(status_code=404, detail="السجل غير موجود")
    db.delete(dup)
    db.commit()
    return Response(status_code=204)


@router.delete("/duplicates", status_code=204)
def clear_duplicates(db: Session = Depends(get_db),
                     _: User = Depends(_editor)) -> Response:
    db.query(Duplicate).delete(synchronize_session=False)
    db.commit()
    return Response(status_code=204)


def _set_status(db: Session, article_id: int, status: ArticleStatus,
                action: PublishAction, user: User, note: str) -> Article:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    article.status = status
    if status == ArticleStatus.published and article.published_at is None:
        article.published_at = datetime.now(timezone.utc)
    _log(db, article.id, action, user, note)
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/publish", response_model=ArticleListItem)
def publish(article_id: int, payload: ArticleActionRequest, db: Session = Depends(get_db),
            user: User = Depends(_editor)):
    return _set_status(db, article_id, ArticleStatus.published, PublishAction.published, user, payload.note)


@router.post("/articles/{article_id}/approve", response_model=ArticleListItem)
def approve(article_id: int, payload: ArticleActionRequest, db: Session = Depends(get_db),
            user: User = Depends(_reviewer)):
    return _set_status(db, article_id, ArticleStatus.published, PublishAction.approved, user, payload.note)


@router.post("/articles/{article_id}/reject", response_model=ArticleListItem)
def reject(article_id: int, payload: ArticleActionRequest, db: Session = Depends(get_db),
           user: User = Depends(_reviewer)):
    return _set_status(db, article_id, ArticleStatus.rejected, PublishAction.rejected, user, payload.note)


@router.post("/articles/{article_id}/unpublish", response_model=ArticleListItem)
def unpublish(article_id: int, payload: ArticleActionRequest, db: Session = Depends(get_db),
              user: User = Depends(_editor)):
    return _set_status(db, article_id, ArticleStatus.unpublished, PublishAction.unpublished, user, payload.note)


@router.post("/articles/{article_id}/correct", response_model=ArticleListItem)
def correct(article_id: int, payload: CorrectionRequest, db: Session = Depends(get_db),
            user: User = Depends(_editor)):
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    if not hasattr(article, payload.field):
        raise HTTPException(status_code=400, detail="الحقل غير صالح")
    previous = getattr(article, payload.field)
    setattr(article, payload.field, payload.new_value)
    if payload.field == "title_ar":
        article.normalized_title = payload.new_value
        article.fingerprint = fingerprint(payload.new_value)
    db.add(Correction(article_id=article.id, user_id=user.id, field=payload.field,
                      previous_value=str(previous or ""), new_value=payload.new_value,
                      reason=payload.reason))
    _log(db, article.id, PublishAction.corrected, user, payload.reason)
    db.commit()
    db.refresh(article)
    return article_to_list_item(article)


@router.get("/classification/flags", response_model=dict)
def classification_monitor(
    db: Session = Depends(get_db),
    _: User = Depends(_reviewer),
    hours: int = Query(default=72, ge=1, le=720),
    limit: int = Query(default=120, ge=1, le=300),
):
    """Monitor the automatic classification of recent articles.

    Re-runs the transparent rule-based classifier against each article and
    flags suspicious assignments (wrong region given the country, missing
    category, low-confidence default «world», or a different detected result).
    """
    from app.ingestion import classify

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = db.scalars(
        select(Article)
        .options(
            selectinload(Article.category),
            selectinload(Article.region),
            selectinload(Article.country),
        )
        .where(
            Article.status == ArticleStatus.published,
            Article.published_at >= since,
            Article.is_generated_summary.is_(True),
            or_(Article.author.is_(None), Article.author.notlike("kairosAI%")),
        )
        .order_by(Article.published_at.desc())
        .limit(limit)
    ).all()

    region_by_country = {
        "LB": "lebanon",
        "SY": "middle-east", "IR": "middle-east", "IQ": "middle-east",
        "PS": "middle-east", "IL": "middle-east", "SA": "middle-east",
        "AE": "middle-east", "QA": "middle-east", "EG": "middle-east",
        "JO": "middle-east", "YE": "middle-east", "TR": "middle-east",
    }

    items = []
    world_keywords = ["دولي", "امريكا", "اوروبا", "روسيا", "الصين", "واشنطن"]
    unsafe_region_hint = "تحتاج مراجعة تحريرية (منطقة الخبر قد تكون مضللة)"
    for a in articles:
        text = f"{a.title_ar or ''} {a.body_ar or ''}"
        detected_category = classify.detect_category(a.title_ar or "", a.body_ar or "")
        detected_country = classify.detect_country(a.title_ar or "", a.body_ar or "")
        cur_category = a.category.slug if a.category else None
        cur_region = a.region.slug if a.region else None
        cur_country = a.country.iso_code if a.country else None

        issues: list[str] = []
        suggested_category: str | None = None
        suggested_region: str | None = None

        if a.category is None:
            issues.append("بلا تصنيف")
            suggested_category = detected_category or None

        if a.region is None and a.country is None:
            if detected_country == "LB":
                issues.append("بلا منطقة بينما الخبر لبناني (الدولة المحددة: LB)")
                suggested_region = "lebanon"
            elif detected_country in region_by_country:
                issues.append(
                    f"بلا منطقة بينما الدولة المحددة ({detected_country}) تقتضي الشرق الأوسط"
                )
                suggested_region = "middle-east"

        if a.region is not None and detected_country and a.region.slug == "world":
            issues.append(unsafe_region_hint)

        if a.category is not None and detected_category and detected_category != cur_category:
            if cur_category == "world" and detected_category != "world":
                issues.append(
                    f"التصنيف الافتراضي «العالم» بينما التصنيف المتوقع: {detected_category}"
                )
                suggested_category = detected_category
            elif detected_category == "world":
                issues.append(unsafe_region_hint if issues else "قد يستحق إعادة تصنيف")

        if (
            a.category is not None
            and cur_category == "world"
            and not detected_category
            and not any(kw in text for kw in world_keywords)
        ):
            issues.append("تصنيف «العالم» بلا دليل واضح في النص")

        if issues:
            items.append(
                {
                    "id": a.id,
                    "title": a.title_ar,
                    "category": cur_category or "",
                    "region": cur_region or "",
                    "country": cur_country or "",
                    "detected_country": detected_country or "",
                    "suggested_category": suggested_category,
                    "suggested_region": suggested_region,
                    "issues": issues,
                }
            )

    return {"count": len(items), "items": items}


@router.patch("/articles/{article_id}/reclassify", response_model=ArticleListItem)
def reclassify_article(
    article_id: int,
    category_slug: str | None = Query(default=None),
    region_slug: str | None = Query(default=None),
    country_iso: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(_editor),
):
    """Apply an editor-blessed classification correction (by slug)."""
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    if category_slug is not None:
        category = db.scalar(select(Category).where(Category.slug == category_slug))
        if category is None:
            raise HTTPException(status_code=400, detail="التصنيف غير موجود")
        article.category_id = category.id
    if region_slug is not None:
        region = db.scalar(select(Region).where(Region.slug == region_slug))
        if region is None:
            raise HTTPException(status_code=400, detail="المنطقة غير موجودة")
        article.region_id = region.id
    if country_iso is not None:
        country = db.scalar(select(Country).where(Country.iso_code == country_iso))
        if country is None:
            raise HTTPException(status_code=400, detail="الدولة غير معروفة")
        article.country_id = country.id
    db.add(Correction(article_id=article.id, user_id=user.id, field="classification",
                      previous_value="", new_value="مُعاد تصنيفه تحريرياً", reason="مراقبة التصنيف"))
    _log(db, article.id, PublishAction.updated, user, "إعادة تصنيف")
    db.commit()
    db.refresh(article)
    return article_to_list_item(article)


@router.get("/articles/{article_id}/logs", response_model=list[PublicationLogOut])
def article_logs(article_id: int, db: Session = Depends(get_db), _: User = Depends(_reviewer)):
    return db.scalars(
        select(PublicationLog).where(PublicationLog.article_id == article_id)
        .order_by(PublicationLog.created_at.desc())
    ).all()


@router.get("/articles/{article_id}/corrections", response_model=list[CorrectionOut])
def article_corrections(article_id: int, db: Session = Depends(get_db), _: User = Depends(_reviewer)):
    return db.scalars(
        select(Correction).where(Correction.article_id == article_id)
        .order_by(Correction.created_at.desc())
    ).all()


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db), _: User = Depends(_reviewer)):
    return db.scalars(select(Source).order_by(Source.trust_tier, Source.name_ar)).all()


@router.post("/sources", response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db), _: User = Depends(_admin)):
    if db.scalar(select(Source).where(Source.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="المعرّف موجود مسبقاً")
    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch("/sources/{source_id}", response_model=SourceOut)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db),
                  _: User = Depends(_admin)):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="المصدر غير موجود")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source


@router.post("/sources/{source_id}/test", response_model=SourceTestResult)
def test_source(source_id: int, db: Session = Depends(get_db), _: User = Depends(_editor)):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="المصدر غير موجود")
    if source.type != SourceType.rss or not source.feed_url:
        return SourceTestResult(ok=False, message="لا يوجد رابط خلاصة صالح للاختبار")
    result = fetch_feed(source.feed_url, max_retries=0)
    if result.ok:
        return SourceTestResult(ok=True, message=f"الخلاصة تعمل ({len(result.items)} عنصر)", entries=len(result.items))
    return SourceTestResult(ok=False, message=result.error)


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
@router.get("/categories", response_model=list[CategoryOut])
def admin_categories(db: Session = Depends(get_db), _: User = Depends(_reviewer)):
    return db.scalars(select(Category).order_by(Category.nav_order)).all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(_admin)):
    if db.scalar(select(Category).where(Category.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="المعرّف موجود مسبقاً")
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# --------------------------------------------------------------------------- #
# Publishing rules
# --------------------------------------------------------------------------- #
@router.get("/rules", response_model=list[RuleOut])
def list_rules(db: Session = Depends(get_db), _: User = Depends(_reviewer)):
    ensure_default_rules(db)
    return db.scalars(select(PublishingRule).order_by(PublishingRule.id)).all()


@router.put("/rules/{key}", response_model=RuleOut)
def update_rule(key: str, payload: RuleUpdate, db: Session = Depends(get_db), _: User = Depends(_admin)):
    rule = set_rule(db, key, payload.value)
    if rule is None:
        raise HTTPException(status_code=404, detail="القاعدة غير موجودة")
    return rule


# --------------------------------------------------------------------------- #
# Ingestion control & logs
# --------------------------------------------------------------------------- #
@router.post("/ingestion/run", response_model=IngestionRunOut)
def trigger_ingestion(db: Session = Depends(get_db), _: User = Depends(_editor)):
    return run_ingestion(db, trigger="manual")


@router.post("/ingestion/pause")
def pause_ingestion(db: Session = Depends(get_db), _: User = Depends(_editor)) -> dict:
    set_rule(db, "ingestion_paused", "true")
    return {"ingestion_enabled": False}


@router.post("/ingestion/resume")
def resume_ingestion(db: Session = Depends(get_db), _: User = Depends(_editor)) -> dict:
    set_rule(db, "ingestion_paused", "false")
    return {"ingestion_enabled": True}


@router.get("/ingestion/state")
def ingestion_state(db: Session = Depends(get_db), _: User = Depends(_reviewer)) -> dict:
    rules = get_rules(db)
    return {"paused": rules.get("ingestion_paused", False),
            "auto_publish_enabled": rules.get("auto_publish_enabled", False)}


@router.get("/runs", response_model=list[IngestionRunOut])
def list_runs(db: Session = Depends(get_db), _: User = Depends(_reviewer),
              limit: int = Query(20, ge=1, le=100)):
    return db.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit)).all()


@router.get("/errors", response_model=list[IngestionErrorOut])
def list_errors(db: Session = Depends(get_db), _: User = Depends(_reviewer),
                limit: int = Query(50, ge=1, le=200)):
    return db.scalars(select(IngestionError).order_by(IngestionError.created_at.desc()).limit(limit)).all()


# --------------------------------------------------------------------------- #
# Users (admin only)
# --------------------------------------------------------------------------- #
@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(_admin)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(_admin)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="البريد مستخدم مسبقاً")
    from app.security import hash_password  # local import to avoid cycles

    user = User(email=payload.email, full_name=payload.full_name, role=payload.role,
                hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db),
                _: User = Depends(_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    data = payload.model_dump(exclude_unset=True)
    if data.get("password"):
        from app.security import hash_password

        user.hashed_password = hash_password(data.pop("password"))
    else:
        data.pop("password", None)
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


# --------------------------------------------------------------------------- #
# kairosAI (تحليل آلي بموقف معلن)
# --------------------------------------------------------------------------- #
@router.post("/kairos/generate", response_model=ArticleListItem)
def kairos_generate(db: Session = Depends(get_db), _: User = Depends(_editor)):
    """توليد/استرجاع تحليل كاييروس للفترة الحالية."""
    from app.kairos import generate_kairos_analysis

    analysis = generate_kairos_analysis(db)
    if analysis is None:
        raise HTTPException(status_code=400, detail="كاييروس معطّل في الإعدادات")
    return article_to_list_item(analysis)


@router.get("/kairos/analyses", response_model=list[ArticleListItem])
def kairos_analyses(db: Session = Depends(get_db), _: User = Depends(_reviewer),
                    limit: int = Query(20, ge=1, le=100)):
    from app.kairos import latest_kairos_analyses

    return [article_to_list_item(a) for a in latest_kairos_analyses(db, limit)]


# --------------------------------------------------------------------------- #
# AI assistant (OpenRouter)
# --------------------------------------------------------------------------- #
@router.get("/ai/status", response_model=AIStatus)
def ai_status(_: User = Depends(_reviewer)) -> AIStatus:
    return AIStatus(**ai.status())


@router.post("/ai/chat", response_model=AIChatResponse)
def ai_chat(payload: AIChatRequest, _: User = Depends(_reviewer)) -> AIChatResponse:
    if not ai.is_configured():
        raise HTTPException(
            status_code=503,
            detail="الذكاء الاصطناعي غير مُفعّل: أضف OPENROUTER_API_KEY في backend/.env",
        )
    messages = [m.model_dump() for m in payload.messages]
    result = ai.admin_assistant(messages, payload.context)
    if result is None:
        raise HTTPException(status_code=502, detail="تعذّر الاتصال بمزوّد الذكاء الاصطناعي.")
    reply, model = result
    return AIChatResponse(reply=reply, model=model)


@router.post("/ai/articles/{article_id}/enrich", response_model=AIEnrichResponse)
def ai_enrich_article(
    article_id: int,
    apply: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(_editor),
) -> AIEnrichResponse:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="الخبر غير موجود")
    if not ai.is_configured():
        raise HTTPException(
            status_code=503,
            detail="الذكاء الاصطناعي غير مُفعّل: أضف OPENROUTER_API_KEY في backend/.env",
        )
    text = article.body_ar or article.summary_ar or article.title_ar
    source_name = article.source.name_ar if article.source else ""
    result = ai.translate_and_summarize(article.title_ar, text, source_name)
    if result is None:
        raise HTTPException(status_code=502, detail="تعذّر توليد النتيجة من مزوّد الذكاء الاصطناعي.")

    if apply:
        article.title_ar = result["title_ar"]
        article.normalized_title = result["title_ar"]
        article.summary_ar = truncate(result["summary_ar"], 320)
        db.add(
            PublicationLog(
                article_id=article.id,
                action=PublishAction.corrected,
                note="تحسين آلي عبر مساعد الذكاء الاصطناعي",
            )
        )
        db.commit()
        db.refresh(article)

    return AIEnrichResponse(
        article_id=article.id,
        title_ar=result["title_ar"],
        summary_ar=result["summary_ar"],
        applied=apply,
        model=settings.ai_model,
    )
