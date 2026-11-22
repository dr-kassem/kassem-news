"""Shared helpers for building API responses from ORM objects."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ingestion import classify
from app.models import Article, ArticleStatus
from app.schemas import ArticleDetail, ArticleListItem


def _load_options():
    return (
        selectinload(Article.category),
        selectinload(Article.region),
        selectinload(Article.source),
        selectinload(Article.tags),
    )


def article_to_list_item(article: Article) -> ArticleListItem:
    return ArticleListItem.model_validate(article)


def article_to_detail(db: Session, article: Article) -> ArticleDetail:
    base = ArticleDetail.model_validate(article)
    base.tags = list(article.tags)
    if article.category_id is not None:
        related = db.scalars(
            select(Article)
            .options(*_load_options())
            .where(
                Article.category_id == article.category_id,
                Article.status == ArticleStatus.published,
                Article.id != article.id,
            )
            .order_by(Article.published_at.desc())
            .limit(4)
        ).all()
    else:
        related = []
    base.related = [article_to_list_item(a) for a in related]
    return base
