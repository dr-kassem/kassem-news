"""Pydantic schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import (
    ArticleStatus,
    PublishAction,
    Role,
    Sensitivity,
    SourceType,
    VerificationStatus,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""
    role: Role = Role.viewer


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


# --- Taxonomy ---
class CategoryOut(ORMModel):
    id: int
    slug: str
    name_ar: str
    name_en: str
    nav_order: int
    show_in_nav: bool


class CategoryCreate(BaseModel):
    slug: str
    name_ar: str
    name_en: str
    nav_order: int = 100
    show_in_nav: bool = True


class RegionOut(ORMModel):
    id: int
    slug: str
    name_ar: str
    name_en: str


class CountryOut(ORMModel):
    id: int
    iso_code: str
    name_ar: str
    name_en: str


class TagOut(ORMModel):
    id: int
    slug: str
    name_ar: str


# --- Sources ---
class SourceBase(BaseModel):
    slug: str
    name_ar: str
    name_en: str
    type: SourceType = SourceType.rss
    feed_url: str
    homepage: str = ""
    language: str = "ar"
    country_iso: str | None = None
    trust_tier: int = Field(default=2, ge=1, le=3)
    requires_review: bool = True
    is_active: bool = True
    fetch_interval_minutes: int = 15
    rights_note: str = ""


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name_ar: str | None = None
    name_en: str | None = None
    feed_url: str | None = None
    homepage: str | None = None
    trust_tier: int | None = Field(default=None, ge=1, le=3)
    requires_review: bool | None = None
    is_active: bool | None = None
    fetch_interval_minutes: int | None = None
    rights_note: str | None = None


class SourceOut(ORMModel, SourceBase):
    id: int
    last_fetched_at: datetime | None
    last_status: str


class SourceTestResult(BaseModel):
    ok: bool
    message: str
    entries: int = 0


# --- Articles ---
class ArticleAuthor(ORMModel):
    id: int
    name_ar: str


class ArticleListItem(ORMModel):
    id: int
    title_ar: str
    summary_ar: str
    url: str
    image_url: str | None
    video_url: str | None
    author: str
    is_breaking: bool
    sensitivity: Sensitivity
    verification_status: VerificationStatus
    status: ArticleStatus
    source_published_at: datetime | None
    published_at: datetime | None
    updated_at: datetime
    category: CategoryOut | None = None
    region: RegionOut | None = None
    source: SourceOut | None = None


class ArticleDetail(ArticleListItem):
    body_ar: str
    tags: list[TagOut] = []
    related: list[ArticleListItem] = []
    event_id: int | None = None
    is_generated_summary: bool = True


class ArticleCreateManual(BaseModel):
    title_ar: str
    summary_ar: str = ""
    body_ar: str = ""
    url: str = ""
    image_url: str | None = None
    video_url: str | None = None
    author: str = ""
    category_id: int | None = None
    region_id: int | None = None
    country_id: int | None = None
    sensitivity: Sensitivity = Sensitivity.normal
    verification_status: VerificationStatus = VerificationStatus.attributed
    is_breaking: bool = False
    publish_now: bool = False


class ArticleUpdate(BaseModel):
    title_ar: str | None = None
    summary_ar: str | None = None
    body_ar: str | None = None
    image_url: str | None = None
    video_url: str | None = None
    category_id: int | None = None
    region_id: int | None = None
    is_breaking: bool | None = None
    sensitivity: Sensitivity | None = None
    verification_status: VerificationStatus | None = None


class ArticleActionRequest(BaseModel):
    note: str = ""


class CorrectionRequest(BaseModel):
    field: str
    new_value: str
    reason: str = ""


# --- Events ---
class EventOut(ORMModel):
    id: int
    title_ar: str
    summary_ar: str
    is_developing: bool
    article_count: int
    first_seen_at: datetime
    last_update_at: datetime


class EventDetail(EventOut):
    timeline: list[ArticleListItem] = []


# --- Publishing rules ---
class RuleOut(ORMModel):
    id: int
    key: str
    value: str
    value_type: str
    label_ar: str
    is_active: bool
    updated_at: datetime


class RuleUpdate(BaseModel):
    value: str


# --- Ingestion dashboard ---
class IngestionRunOut(ORMModel):
    id: int
    trigger: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    sources_total: int
    sources_ok: int
    sources_failed: int
    articles_fetched: int
    articles_new: int
    articles_published: int
    articles_review: int
    duplicates: int
    errors: int
    notes: str


class IngestionErrorOut(ORMModel):
    id: int
    run_id: int | None
    source_id: int | None
    message: str
    retry_count: int
    created_at: datetime


class DashboardStats(BaseModel):
    total_articles: int
    published: int
    pending_review: int
    duplicates_detected: int
    failed_fetches: int
    active_sources: int
    total_sources: int
    total_events: int
    last_run: IngestionRunOut | None
    recent_runs: list[IngestionRunOut]
    recent_errors: list[IngestionErrorOut]


class PublicationLogOut(ORMModel):
    id: int
    article_id: int
    action: PublishAction
    actor_user_id: int | None
    note: str
    created_at: datetime


class CorrectionOut(ORMModel):
    id: int
    article_id: int
    field: str
    previous_value: str
    new_value: str
    reason: str
    created_at: datetime


class PipelineState(BaseModel):
    ingestion_enabled: bool
    paused_reason: str = ""


class AIChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=8000)


class AIChatRequest(BaseModel):
    messages: list[AIChatMessage] = Field(min_length=1)
    context: str = ""


class AIChatResponse(BaseModel):
    reply: str
    model: str


class AIEnrichResponse(BaseModel):
    article_id: int
    title_ar: str
    summary_ar: str
    applied: bool
    model: str


class AIStatus(BaseModel):
    enabled: bool
    configured: bool
    provider: str
    model: str
    fallback_models: list[str]
    summarize_on_ingest: bool


class PublicAssistantMessage(BaseModel):
    role: str = "user"
    content: str = Field(min_length=1, max_length=1500)


class PublicAssistantRequest(BaseModel):
    messages: list[PublicAssistantMessage] = Field(min_length=1, max_length=10)
