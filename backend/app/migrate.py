"""Lightweight, idempotent schema migrations for existing databases.

The project relies on ``Base.metadata.create_all`` for fresh databases, but that
never alters existing tables. This module adds columns introduced after a
database was first created and backfills their values once.
"""
from __future__ import annotations

import logging

from sqlalchemy import Engine, inspect, select, text
from sqlalchemy.orm import Session

from app.ingestion import classify
from app.models import Article, Source

logger = logging.getLogger("kassem.migrate")


def _column_exists(engine: Engine, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspect(engine).get_columns(table)}


def _add_is_strike(engine: Engine, db: Session) -> None:
    if _column_exists(engine, "articles", "is_strike"):
        return
    is_sqlite = engine.dialect.name == "sqlite"
    ddl = (
        "ALTER TABLE articles ADD COLUMN is_strike BOOLEAN DEFAULT 0"
        if is_sqlite
        else "ALTER TABLE articles ADD COLUMN IF NOT EXISTS is_strike BOOLEAN DEFAULT false"
    )
    with engine.begin() as conn:
        conn.execute(text(ddl))
    logger.info("migration: added articles.is_strike")

    articles = db.scalars(select(Article)).all()
    for article in articles:
        article.is_strike = classify.is_strike(article.title_ar or "", article.summary_ar or "")
    db.commit()
    logger.info("migration: backfilled is_strike for %d articles", len(articles))


def _add_video_url(engine: Engine) -> None:
    if _column_exists(engine, "articles", "video_url"):
        return
    is_sqlite = engine.dialect.name == "sqlite"
    ddl = (
        "ALTER TABLE articles ADD COLUMN video_url VARCHAR(1500)"
        if is_sqlite
        else "ALTER TABLE articles ADD COLUMN IF NOT EXISTS video_url VARCHAR(1500)"
    )
    with engine.begin() as conn:
        conn.execute(text(ddl))
    logger.info("migration: added articles.video_url")


def _rebrand_google_search_sources(db: Session) -> None:
    rows = db.scalars(select(Source).where(Source.name_ar.like("%بحث جوجل%"))).all()
    if not rows:
        return
    for source in rows:
        source.name_ar = "قاسم نيوز"
        source.name_en = "Kassem News"
    db.commit()
    logger.info("migration: rebranded %d Google search source(s)", len(rows))


def run_migrations(engine: Engine, db: Session) -> None:
    _add_is_strike(engine, db)
    _add_video_url(engine)
    _rebrand_google_search_sources(db)
