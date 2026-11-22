from datetime import datetime, timedelta, timezone

from app.models import ArticleStatus, Sensitivity
from app.publishing import evaluate


def _rules():
    return {
        "auto_publish_enabled": True,
        "sensitive_requires_review": True,
        "breaking_requires_review": True,
        "min_source_trust": 2,
        "max_age_hours": 72,
        "min_title_length": 15,
        "require_image": False,
        "auto_publish_categories": ["politics", "economy", "technology", "cybersecurity", "world", "analysis"],
    }


class FakeSource:
    def __init__(self, trust_tier=1, requires_review=False):
        self.trust_tier = trust_tier
        self.requires_review = requires_review


def test_routine_news_publishes_automatically():
    decision = evaluate(
        FakeSource(),
        _rules(),
        title="البنك المركزي يقرر رفع أسعار الفائدة الأساسية",
        category_slug="economy",
    )
    assert decision.status == ArticleStatus.published
    assert decision.is_sensitive is False


def test_sensitive_news_routed_to_review():
    decision = evaluate(
        FakeSource(),
        _rules(),
        title="غارة إسرائيلية على الضاحية في بيروت تسفر عن قتلى وجرحى",
        category_slug="world",
    )
    assert decision.status == ArticleStatus.review
    assert decision.is_sensitive is True
    assert decision.verification_status.value == "developing"


def test_breaking_news_routed_to_review():
    decision = evaluate(
        FakeSource(),
        _rules(),
        title="عاجل: انفجار قوي يهز وسط العاصمة بيروت",
        category_slug="world",
    )
    assert decision.status == ArticleStatus.review
    assert decision.is_breaking is True


def test_low_trust_source_routed_to_review():
    decision = evaluate(
        FakeSource(trust_tier=3),
        _rules(),
        title="تقرير حول آفاق الطاقة المتجددة في المنطقة",
        category_slug="economy",
    )
    assert decision.status == ArticleStatus.review


def test_source_requiring_review_routed_to_review():
    decision = evaluate(
        FakeSource(requires_review=True),
        _rules(),
        title="نتائج قمة اقتصادية إقليمية حول التجارة الحرة",
        category_slug="economy",
    )
    assert decision.status == ArticleStatus.review


def test_category_outside_auto_publish_routed_to_review():
    decision = evaluate(
        FakeSource(),
        _rules(),
        title="مهرجان سينمائي جديد ينطلق في تونس",
        category_slug="culture",
    )
    assert decision.status == ArticleStatus.review


def test_stale_news_routed_to_review():
    old = datetime.now(timezone.utc) - timedelta(days=5)
    decision = evaluate(
        FakeSource(),
        _rules(),
        title="البنك المركزي يقرر رفع أسعار الفائدة الأساسية",
        category_slug="economy",
        published_at=old,
    )
    assert decision.status == ArticleStatus.review


def test_auto_publish_disabled_sends_to_review():
    rules = _rules()
    rules["auto_publish_enabled"] = False
    decision = evaluate(
        FakeSource(),
        rules,
        title="البنك المركزي يقرر رفع أسعار الفائدة الأساسية",
        category_slug="economy",
    )
    assert decision.status == ArticleStatus.review


def test_auto_publish_all_publishes_everything():
    rules = _rules()
    rules["auto_publish_all"] = True
    # Even a sensitive, low-trust, stale item is accepted automatically.
    old = datetime.now(timezone.utc) - timedelta(days=5)
    decision = evaluate(
        FakeSource(trust_tier=3, requires_review=True),
        rules,
        title="عاجل: غارة إسرائيلية على الضاحية في بيروت تسفر عن قتلى وجرحى",
        category_slug="world",
        published_at=old,
    )
    assert decision.status == ArticleStatus.published
    assert decision.is_sensitive is True
    assert decision.is_breaking is True
