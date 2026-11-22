from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.ingestion.fetch import FetchedItem, FetchResult
from app.ingestion.pipeline import run_ingestion
from app.models import Article, ArticleStatus, Duplicate, Event
from app.publishing import ensure_default_rules, set_rule


def _item(url: str, title: str, published_at=None) -> FetchedItem:
    return FetchedItem(
        title=title,
        url=url,
        summary="ملخص من المصدر الأصلي.",
        author="وكالة أملاك",
        published_at=published_at or datetime.now(timezone.utc),
    )


def test_pipeline_routes_duplicates_and_events(db, seed_data, monkeypatch):
    ensure_default_rules(db)
    # Exercise the granular routing rules; the global auto-publish-all switch
    # is covered separately in test_publishing.py.
    set_rule(db, "auto_publish_all", "false")
    source = seed_data["source"]

    SINKS = [
        _item("https://ex.test/a1", "غارة إسرائيلية على الضاحية في بيروت تسفر عن قتلى وجرحى"),
        _item("https://ex.test/a2", "البنك المركزي يقرر رفع أسعار الفائدة الأساسية"),
        _item("https://ex.test/a3", "المركزي يقرر رفع أسعار الفائدة الأساسية اليوم في بيروت"),
        _item("https://ex.test/a4", "غارة جديدة تستهدف الضاحية الجنوبية في بيروت وتوقع ضحايا"),
        _item(
            "https://ex.test/a5",
            "البنك المركزي يخفض الاحتياطي من العملة في قرار تاريخي",
            published_at=datetime.now(timezone.utc) - timedelta(days=5),
        ),
    ]

    def fake_fetch(feed_url, max_retries=None):
        return FetchResult(ok=True, items=SINKS)

    monkeypatch.setattr("app.ingestion.pipeline.fetch_feed", fake_fetch)

    run = run_ingestion(db, trigger="manual", source_ids=[source.id])

    assert run.duplicates == 1
    assert run.articles_new == 4
    assert run.articles_published == 1
    assert run.articles_review == 3

    published = db.scalars(
        select(Article).where(Article.status == ArticleStatus.published)
    ).all()
    assert len(published) == 1
    assert "الفائدة" in published[0].title_ar

    dup = db.scalars(select(Duplicate)).all()
    assert len(dup) == 1
    assert dup[0].duplicate_of_id in {a.id for a in published}

    strike_articles = db.scalars(
        select(Article).where(Article.title_ar.contains("الضاحية"))
    ).all()
    assert len(strike_articles) == 2
    event_ids = {a.event_id for a in strike_articles}
    assert len(event_ids) == 1
    event = db.get(Event, strike_articles[0].event_id)
    assert event is not None
    assert event.article_count >= 2


def test_pipeline_records_fetch_failure(db, seed_data, monkeypatch):
    ensure_default_rules(db)
    source = seed_data["source"]

    def failing_fetch(feed_url, max_retries=None):
        return FetchResult(ok=False, items=[], error="HTTP 500", retries=2)

    monkeypatch.setattr("app.ingestion.pipeline.fetch_feed", failing_fetch)
    run = run_ingestion(db, trigger="manual", source_ids=[source.id])

    assert run.sources_failed == 1
    assert run.errors >= 1
    assert "HTTP 500" in run.notes or run.articles_new == 0