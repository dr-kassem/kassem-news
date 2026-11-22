"""Public, read-only API used by the website frontend."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app import __version__, ai
from app.api.helpers import _load_options, article_to_detail, article_to_list_item
from app.config import settings
from app.database import get_db
from app.deps import Pagination, get_pagination
from app.kairos import latest_kairos_analyses
from app.strikes import fetch_reports, type_label
from app.models import (
    Article,
    ArticleStatus,
    Category,
    Country,
    Event,
    EventArticle,
    NewsletterSubscriber,
    Region,
    Source,
)
from app.schemas import (
    AIChatResponse,
    ArticleDetail,
    ArticleListItem,
    CategoryOut,
    CountryOut,
    EventDetail,
    EventOut,
    PublicAssistantRequest,
    RegionOut,
    SourceOut,
)

router = APIRouter(prefix="/api", tags=["public"])

PUBLISHED = Article.status == ArticleStatus.published


def _published_query():
    return (
        select(Article)
        .options(*_load_options())
        .where(PUBLISHED)
        .order_by(func.coalesce(Article.published_at, Article.received_at).desc())
    )


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": __version__,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/meta")
def meta(db: Session = Depends(get_db)) -> dict:
    categories = db.scalars(select(Category).order_by(Category.nav_order)).all()
    regions = db.scalars(select(Region).order_by(Region.id)).all()
    return {
        "app_name": settings.app_name,
        "slogan_ar": settings.app_slogan_ar,
        "slogan_en": settings.app_slogan_en,
        "categories": [CategoryOut.model_validate(c) for c in categories],
        "regions": [RegionOut.model_validate(r) for r in regions],
    }


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.nav_order)).all()


@router.get("/regions", response_model=list[RegionOut])
def list_regions(db: Session = Depends(get_db)):
    return db.scalars(select(Region).order_by(Region.id)).all()


@router.get("/countries", response_model=list[CountryOut])
def list_countries(db: Session = Depends(get_db)):
    return db.scalars(select(Country).order_by(Country.name_ar)).all()


@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.scalars(
        select(Source).where(Source.is_active.is_(True)).order_by(Source.trust_tier)
    ).all()


class ArticlePage(BaseModel):
    items: list[ArticleListItem]
    page: int
    page_size: int
    total: int
    pages: int


@router.get("/articles", response_model=ArticlePage)
def list_articles(
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
    category: str | None = Query(default=None),
    region: str | None = Query(default=None),
    source: str | None = Query(default=None),
    country: str | None = Query(default=None),
    q: str | None = Query(default=None),
    breaking: bool | None = Query(default=None),
    strike: bool | None = Query(default=None),
    event_id: int | None = Query(default=None),
):
    query = _published_query()
    count_query = select(func.count(Article.id)).where(PUBLISHED)

    def apply(stmt):
        if category:
            stmt = stmt.join(Category, isouter=True).where(Category.slug == category)
        if region:
            stmt = stmt.join(Region, isouter=True).where(Region.slug == region)
        if country:
            stmt = stmt.join(Country, isouter=True).where(Country.iso_code == country)
        if source:
            stmt = stmt.join(Source, isouter=True).where(Source.slug == source)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(Article.title_ar.ilike(like), Article.summary_ar.ilike(like)))
        if breaking is not None:
            stmt = stmt.where(Article.is_breaking.is_(breaking))
        if strike is not None:
            stmt = stmt.where(Article.is_strike.is_(strike))
        if event_id:
            stmt = stmt.where(Article.event_id == event_id)
        return stmt

    query = apply(query)
    count_query = apply(count_query)
    total = db.scalar(count_query) or 0
    rows = db.scalars(query.offset(pagination.offset).limit(pagination.limit)).all()
    return ArticlePage(
        items=[article_to_list_item(a) for a in rows],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
        pages=max((total + pagination.page_size - 1) // pagination.page_size, 1),
    )


@router.get("/breaking", response_model=list[ArticleListItem])
def breaking(db: Session = Depends(get_db), limit: int = Query(6, ge=1, le=20)):
    rows = db.scalars(_published_query().where(Article.is_breaking.is_(True)).limit(limit)).all()
    return [article_to_list_item(a) for a in rows]


class StrikeReport(BaseModel):
    id: str
    short_code: str
    type: str
    type_label: str
    category: str
    city_name: str
    description: str
    lat: float | None = None
    lon: float | None = None
    created_at: str
    approximate_location: bool
    location_precision_m: int | None = None
    evidence_label: str


class StrikeTypeCount(BaseModel):
    type: str
    label: str
    count: int


class StrikeFeed(BaseModel):
    items: list[StrikeReport]
    types: list[StrikeTypeCount]
    total: int
    page: int
    page_size: int
    pages: int
    updated_at: str | None = None


@router.get("/strikes", response_model=StrikeFeed)
def strikes_feed(
    event_type: str | None = Query(default=None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=60),
):
    """رصد ميداني مباشر للغارات والقصف والمسيّرات لقسم «الغارات».

    The feed is sourced from the ajwa2.com public field-report API (Lebanon) and
    presented under the platform's own attribution. Short-lived upstream caching
    keeps request volume well within the provider's rate limits.
    """
    reports, cached_at = fetch_reports()

    counts: dict[str, int] = {}
    for report in reports:
        counts[report["type"]] = counts.get(report["type"], 0) + 1
    types = [
        StrikeTypeCount(type=code, label=type_label(code), count=count)
        for code, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    filtered = [r for r in reports if r["type"] == event_type] if event_type else reports
    total = len(filtered)
    start = (page - 1) * page_size
    window = filtered[start : start + page_size]
    updated_at = (
        datetime.fromtimestamp(cached_at, tz=timezone.utc).isoformat()
        if cached_at
        else None
    )
    return StrikeFeed(
        items=[StrikeReport(**r) for r in window],
        types=types,
        total=total,
        page=page,
        page_size=page_size,
        pages=max((total + page_size - 1) // page_size, 1),
        updated_at=updated_at,
    )


@router.get("/most-read", response_model=list[ArticleListItem])
def most_read(db: Session = Depends(get_db), limit: int = Query(6, ge=1, le=20)):
    rows = db.scalars(
        select(Article).options(*_load_options()).where(PUBLISHED)
        .order_by(Article.view_count.desc(),
                  func.coalesce(Article.published_at, Article.received_at).desc())
        .limit(limit)
    ).all()
    return [article_to_list_item(a) for a in rows]


@router.get("/on-this-day", response_model=list[ArticleListItem])
def on_this_day(db: Session = Depends(get_db), limit: int = Query(12, ge=1, le=40)):
    now = datetime.now(timezone.utc)
    rows = db.scalars(
        select(Article).options(*_load_options()).where(
            PUBLISHED,
            func.extract("month", Article.published_at) == now.month,
            func.extract("day", Article.published_at) == now.day,
            func.extract("year", Article.published_at) != now.year,
        )
        .order_by(Article.published_at.desc())
        .limit(limit)
    ).all()
    return [article_to_list_item(a) for a in rows]


@router.get("/lead", response_model=ArticleListItem | None)
def lead(db: Session = Depends(get_db)):
    row = db.scalar(_published_query().where(Article.image_url.is_not(None)).limit(1))
    if row is None:
        row = db.scalar(_published_query().limit(1))
    return article_to_list_item(row) if row else None


@router.get("/articles/{article_id}", response_model=ArticleDetail)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.scalar(
        select(Article).options(*_load_options()).where(
            Article.id == article_id, PUBLISHED
        )
    )
    if article is None:
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    article.view_count = (article.view_count or 0) + 1
    db.commit()
    db.refresh(article)
    return article_to_detail(db, article)


@router.get("/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db), limit: int = Query(10, ge=1, le=50)):
    return db.scalars(
        select(Event).order_by(Event.last_update_at.desc()).limit(limit)
    ).all()


@router.get("/kairos", response_model=list[ArticleListItem])
def list_kairos_analyses(db: Session = Depends(get_db), limit: int = Query(6, ge=1, le=20)):
    """تحليلات كاييروس إيه آي — محلل المنصة الآلي بموقفه المعلن."""
    return [article_to_list_item(a) for a in latest_kairos_analyses(db, limit)]


class KairosStateOut(BaseModel):
    enabled: bool
    author: str
    stance: str
    interval_hours: int


@router.get("/kairos/state", response_model=KairosStateOut)
def kairos_state():
    return KairosStateOut(
        enabled=settings.kairos_enabled,
        author=settings.kairos_author,
        stance=settings.kairos_stance,
        interval_hours=settings.kairos_interval_hours,
    )


@router.get("/events/{event_id}", response_model=EventDetail)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="الحدث غير موجود")
    rows = db.scalars(
        select(Article).options(*_load_options())
        .join(EventArticle, EventArticle.article_id == Article.id)
        .where(EventArticle.event_id == event_id, PUBLISHED)
        .order_by(func.coalesce(Article.published_at, Article.received_at).desc())
    ).all()
    detail = EventDetail.model_validate(event)
    detail.timeline = [article_to_list_item(a) for a in rows]
    return detail


class NewsletterRequest(BaseModel):
    email: EmailStr
    language: str = "ar"


@router.post("/newsletter", status_code=201)
def subscribe(payload: NewsletterRequest, db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == payload.email)
    )
    if existing:
        return {"ok": True, "message": "البريد مسجل مسبقاً"}
    db.add(NewsletterSubscriber(email=payload.email, language=payload.language))
    db.commit()
    return {"ok": True, "message": "تم تسجيل اشتراكك بنجاح"}


@router.get("/assistant/status")
def assistant_status() -> dict:
    return {"enabled": bool(settings.ai_enabled), "configured": settings.ai_configured}


@router.post("/assistant/chat", response_model=AIChatResponse)
def assistant_chat(
    payload: PublicAssistantRequest, db: Session = Depends(get_db)
) -> AIChatResponse:
    if not ai.is_configured():
        raise HTTPException(
            status_code=503,
            detail="مساعد قاسم نيوز غير متاح حالياً. حاول لاحقاً.",
        )

    messages = [
        {
            "role": message.role if message.role in ("user", "assistant") else "user",
            "content": message.content.strip(),
        }
        for message in payload.messages
        if message.content.strip()
    ]
    if not messages:
        raise HTTPException(status_code=400, detail="لا توجد رسائل صالحة.")

    rows = db.scalars(
        select(Article)
        .where(PUBLISHED)
        .order_by(func.coalesce(Article.published_at, Article.received_at).desc())
        .limit(8)
    ).all()
    context = "\n".join(
        f"- {article.title_ar}: {article.summary_ar}"
        for article in rows
        if getattr(article, "title_ar", None)
    )

    result = ai.public_assistant(messages, context)
    if result is None:
        raise HTTPException(
            status_code=502,
            detail="تعذّر الحصول على رد الآن. حاول بعد قليل.",
        )
    reply, model = result
    return AIChatResponse(reply=reply, model=model)
