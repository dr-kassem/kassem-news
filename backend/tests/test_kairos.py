"""Tests for the kairosAI automatic analyst (analysis with declared stance)."""
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.kairos import KAIROS_MARKER, generate_kairos_analysis, latest_kairos_analyses
from app.models import Article, ArticleStatus, Event


def test_generate_kairos_analysis(db, seed_data):
    # seed some real published articles and an event so the analysis has data
    now = datetime.now(timezone.utc)
    cat = seed_data["category"]["politics"]
    lebanon = seed_data["region"]["lebanon"]
    source = seed_data["source"]

    titles = [
        "المقاومة تؤكد جهوزيتها في الجنوب وتصعّد الردع",
        "طهران تعلن دعمها الكامل لمحور المقاومة",
        "العدو يهدد بشن عملية برية واسعة",
    ]
    for i, t in enumerate(titles):
        a = Article(
            source_id=source.id,
            category_id=cat,
            region_id=lebanon.id,
            title_ar=t,
            normalized_title=t,
            fingerprint=f"kairos-fixture-{i}",
            summary_ar=t,
            body_ar=t,
            url=f"https://example.test/k{i}",
            url_hash=f"h{i}" * 16,
            status=ArticleStatus.published,
            published_at=now,
        )
        db.add(a)
    db.add(Event(title_ar="اشتباكات على الحدود الجنوبية", article_count=3))
    db.commit()

    analysis = generate_kairos_analysis(db)
    assert analysis is not None
    assert analysis.author.startswith(KAIROS_MARKER)
    assert analysis.status == ArticleStatus.published
    assert analysis.title_ar.startswith("تحليل كاييروس")
    assert "إرهاب" not in analysis.body_ar  # banned terms never appear
    assert analysis.body_ar.count("كاييروس") > 0
    assert "الانحياز إلى محور المقاومة" in analysis.body_ar  # declared stance disclosed
    assert "أنصار الله" in analysis.body_ar  # Yemen resistance named explicitly
    assert "المقاومة العراقية" in analysis.body_ar  # Iraq resistance named explicitly
    assert "تطورات" in analysis.summary_ar

    # idempotent — same window returns the same analysis (no duplicates)
    again = generate_kairos_analysis(db)
    assert again.id == analysis.id
    assert db.scalar(select(func.count(Article.id))) == 4


def test_latest_kairos_only_returns_marked_articles(db, seed_data):
    db.add(Article(
        title_ar="خبر عادي",
        normalized_title="خبر عادي",
        fingerprint="plain",
        summary_ar="",
        body_ar="",
        url="https://example.test/plain",
        url_hash="p" * 32,
        status=ArticleStatus.published,
        published_at=datetime.now(timezone.utc),
    ))
    generate_kairos_analysis(db)
    db.commit()
    items = latest_kairos_analyses(db)
    assert items, "expected at least the generated analysis"
    assert all(a.author.startswith(KAIROS_MARKER) for a in items)


def test_kairos_drops_banned_quoted_headlines(db, seed_data):
    """Headlines carrying loaded terms such as «إرهابي» must never be quoted."""
    now = datetime.now(timezone.utc)
    source = seed_data["source"]
    banned = Article(
        source_id=source.id,
        title_ar="إرهابيون يستهدفون مطار الرياض",
        normalized_title="إرهابيون يستهدفون مطار الرياض",
        fingerprint="kairos-banned",
        summary_ar="إرهابيون يستهدفون مطار الرياض",
        body_ar="إرهابيون يستهدفون مطار الرياض",
        url="https://example.test/banned",
        url_hash="b" * 32,
        status=ArticleStatus.published,
        published_at=now,
    )
    db.add(banned)
    db.commit()

    analysis = generate_kairos_analysis(db)
    assert analysis is not None
    assert "إرهابي" not in analysis.body_ar
    assert "إرهابيون" not in analysis.body_ar