"""SQLAlchemy ORM models for KASSEM NEWS."""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    reviewer = "reviewer"
    viewer = "viewer"


class SourceType(str, enum.Enum):
    rss = "rss"
    api = "api"


class ArticleStatus(str, enum.Enum):
    pending = "pending"       # collected, not yet evaluated
    review = "review"         # awaiting human review
    published = "published"   # live on the site
    rejected = "rejected"     # discarded
    unpublished = "unpublished"  # removed after being live


class Sensitivity(str, enum.Enum):
    normal = "normal"
    sensitive = "sensitive"


class VerificationStatus(str, enum.Enum):
    confirmed = "confirmed"       # independently confirmed by the platform
    attributed = "attributed"     # reported as a claim attributed to a source
    developing = "developing"     # ongoing event, facts may change
    unconfirmed = "unconfirmed"   # single unverified report


class RunStatus(str, enum.Enum):
    running = "running"
    success = "success"
    partial = "partial"
    failed = "failed"


class PublishAction(str, enum.Enum):
    created = "created"
    published = "published"
    approved = "approved"
    rejected = "rejected"
    unpublished = "unpublished"
    corrected = "corrected"
    updated = "updated"


article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.viewer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ar: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))

    countries: Mapped[list["Country"]] = relationship(back_populates="region")


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    iso_code: Mapped[str] = mapped_column(String(2), unique=True, index=True)
    name_ar: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id"), nullable=True)

    region: Mapped[Region | None] = relationship(back_populates="countries")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ar: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    nav_order: Mapped[int] = mapped_column(Integer, default=100)
    show_in_nav: Mapped[bool] = mapped_column(Boolean, default=True)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ar: Mapped[str] = mapped_column(String(128))


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ar: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200))
    type: Mapped[SourceType] = mapped_column(Enum(SourceType), default=SourceType.rss)
    feed_url: Mapped[str] = mapped_column(String(1000))
    homepage: Mapped[str] = mapped_column(String(1000), default="")
    language: Mapped[str] = mapped_column(String(8), default="ar")
    country_iso: Mapped[str | None] = mapped_column(String(2), nullable=True)
    trust_tier: Mapped[int] = mapped_column(Integer, default=2)  # 1 highest .. 3 lowest
    requires_review: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    rights_note: Mapped[str] = mapped_column(String(500), default="")
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str] = mapped_column(String(200), default="never")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    articles: Mapped[list["Article"]] = relationship(back_populates="source")


class Event(Base):
    """A cluster of articles describing the same real-world event."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title_ar: Mapped[str] = mapped_column(String(500))
    summary_ar: Mapped[str] = mapped_column(Text, default="")
    is_developing: Mapped[bool] = mapped_column(Boolean, default=True)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_update_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_articles_url_hash"),
        Index("ix_articles_status_published", "status", "published_at"),
        Index("ix_articles_category", "category_id"),
        Index("ix_articles_region", "region_id"),
        Index("ix_articles_fingerprint", "fingerprint"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id"), nullable=True)
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"), nullable=True)

    title_ar: Mapped[str] = mapped_column(String(500))
    normalized_title: Mapped[str] = mapped_column(String(500), default="")
    fingerprint: Mapped[str] = mapped_column(String(64), default="")

    summary_ar: Mapped[str] = mapped_column(Text, default="")
    body_ar: Mapped[str] = mapped_column(Text, default="")

    url: Mapped[str] = mapped_column(String(1500))
    url_hash: Mapped[str] = mapped_column(String(64))
    image_url: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    author: Mapped[str] = mapped_column(String(300), default="")

    language: Mapped[str] = mapped_column(String(8), default="ar")
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus), default=ArticleStatus.pending, index=True
    )
    sensitivity: Mapped[Sensitivity] = mapped_column(
        Enum(Sensitivity), default=Sensitivity.normal, index=True
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.attributed
    )
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_strike: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_generated_summary: Mapped[bool] = mapped_column(Boolean, default=True)

    source_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    source: Mapped[Source | None] = relationship(back_populates="articles")
    category: Mapped[Category | None] = relationship()
    region: Mapped[Region | None] = relationship()
    country: Mapped[Country | None] = relationship()
    event: Mapped[Event | None] = relationship()
    tags: Mapped[list[Tag]] = relationship(secondary=article_tags)

    @property
    def has_image(self) -> bool:
        return bool(self.image_url)

    @property
    def has_video(self) -> bool:
        return bool(self.video_url)


class EventArticle(Base):
    __tablename__ = "event_articles"
    __table_args__ = (
        UniqueConstraint("event_id", "article_id", name="uq_event_article"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"))
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Duplicate(Base):
    """Records that a collected article was a near-duplicate of an existing one."""

    __tablename__ = "duplicates"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    url: Mapped[str] = mapped_column(String(1500), default="")
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PublicationLog(Base):
    __tablename__ = "publication_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), index=True)
    action: Mapped[PublishAction] = mapped_column(Enum(PublishAction))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Correction(Base):
    __tablename__ = "corrections"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    field: Mapped[str] = mapped_column(String(64))
    previous_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    trigger: Mapped[str] = mapped_column(String(32), default="scheduled")
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.running)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sources_total: Mapped[int] = mapped_column(Integer, default=0)
    sources_ok: Mapped[int] = mapped_column(Integer, default=0)
    sources_failed: Mapped[int] = mapped_column(Integer, default=0)
    articles_fetched: Mapped[int] = mapped_column(Integer, default=0)
    articles_new: Mapped[int] = mapped_column(Integer, default=0)
    articles_published: Mapped[int] = mapped_column(Integer, default=0)
    articles_review: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="SET NULL"), nullable=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(8), default="ar")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PublishingRule(Base):
    __tablename__ = "publishing_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    value_type: Mapped[str] = mapped_column(String(16), default="string")
    label_ar: Mapped[str] = mapped_column(String(200), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
