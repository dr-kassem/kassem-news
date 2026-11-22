"""Configurable publishing-rule engine.

Rules live in the database (`publishing_rules`) so editors can change behaviour
without a redeploy. This module is the single source of truth for the decision
of whether a collected article is published automatically, sent to review, or
rejected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion import classify, dedupe
from app.models import ArticleStatus, PublishingRule, Sensitivity, Source, VerificationStatus


DEFAULTS: list[dict] = [
    {"key": "auto_publish_enabled", "value": "true", "value_type": "bool",
     "label_ar": "تمكين النشر التلقائي للأخبار الروتينية"},
    {"key": "auto_publish_all", "value": "true", "value_type": "bool",
     "label_ar": "قبول ونشر كل الأخبار تلقائياً (دون مراجعة)"},
    {"key": "sensitive_requires_review", "value": "true", "value_type": "bool",
     "label_ar": "إحالة الأخبار الحساسة إلى المراجعة"},
    {"key": "breaking_requires_review", "value": "true", "value_type": "bool",
     "label_ar": "إحالة أخبار العاجل إلى المراجعة"},
    {"key": "min_source_trust", "value": "2", "value_type": "int",
     "label_ar": "أعلى رقم ثقة مقبول للمصدر (1=الأعلى)"},
    {"key": "max_age_hours", "value": "72", "value_type": "int",
     "label_ar": "أقصى عمر للخبر بالساعات قبل إحالته للمراجعة"},
    {"key": "min_title_length", "value": "15", "value_type": "int",
     "label_ar": "أدنى طول للعنوان"},
    {"key": "require_image", "value": "false", "value_type": "bool",
     "label_ar": "اشتراط وجود صورة للنشر التلقائي"},
    {"key": "duplicate_threshold", "value": str(dedupe.DUPLICATE_THRESHOLD), "value_type": "float",
     "label_ar": "عتبة اعتبار الخبر مكرراً"},
    {"key": "event_threshold", "value": str(dedupe.EVENT_THRESHOLD), "value_type": "float",
     "label_ar": "عتبة تجميع الأخبار في حدث واحد"},
    {"key": "auto_publish_categories", "value": "politics,economy,technology,cybersecurity,world,analysis",
     "value_type": "csv", "label_ar": "الأقسام المسموح بنشرها تلقائياً"},
    {"key": "ingestion_paused", "value": "false", "value_type": "bool",
     "label_ar": "إيقاف خط التوريد مؤقتاً"},
]


def _coerce(value: str, value_type: str):
    if value_type == "bool":
        return str(value).strip().lower() in ("1", "true", "yes", "on")
    if value_type == "int":
        return int(value)
    if value_type == "float":
        return float(value)
    if value_type == "csv":
        return [v.strip() for v in str(value).split(",") if v.strip()]
    return value


def ensure_default_rules(db: Session) -> None:
    existing = {r.key for r in db.scalars(select(PublishingRule)).all()}
    for default in DEFAULTS:
        if default["key"] not in existing:
            db.add(PublishingRule(**default))
    db.commit()


def get_rules(db: Session, ensure: bool = True) -> dict:
    if ensure:
        ensure_default_rules(db)
    rules = db.scalars(select(PublishingRule)).all()
    return {
        r.key: _coerce(r.value, r.value_type)
        for r in rules
        if r.is_active
    }


def set_rule(db: Session, key: str, value: str) -> PublishingRule | None:
    rule = db.scalar(select(PublishingRule).where(PublishingRule.key == key))
    if rule is None:
        return None
    rule.value = value
    db.commit()
    db.refresh(rule)
    return rule


@dataclass
class Decision:
    status: ArticleStatus
    verification_status: VerificationStatus = VerificationStatus.attributed
    is_breaking: bool = False
    is_sensitive: bool = False
    reasons: list[str] = field(default_factory=list)


def evaluate(source: Source | None, rules: dict, *, title: str, body: str = "",
             has_image: bool = False, category_slug: str | None = None,
             published_at: datetime | None = None) -> Decision:
    """Decide the routing for a single collected article."""
    reasons: list[str] = []

    is_breaking = classify.is_breaking(title)
    sensitivity = classify.detect_sensitivity(title, body)
    is_sensitive = sensitivity == Sensitivity.sensitive

    decision = Decision(
        status=ArticleStatus.pending,
        verification_status=VerificationStatus.developing if is_sensitive else VerificationStatus.attributed,
        is_breaking=is_breaking,
        is_sensitive=is_sensitive,
    )

    # Global switch: accept and publish every collected item automatically.
    # Editors can still edit or delete any article afterwards.
    if rules.get("auto_publish_all"):
        decision.status = ArticleStatus.published
        decision.reasons.append("قبول تلقائي لكل الأخبار")
        return decision

    if len(title.strip()) < rules["min_title_length"]:
        decision.status = ArticleStatus.review
        decision.reasons.append("العنوان قصير جداً")
        return decision

    if published_at is not None:
        age = datetime.now(timezone.utc) - published_at
        if age > timedelta(hours=rules["max_age_hours"]):
            decision.status = ArticleStatus.review
            decision.reasons.append("الخبر قديم ويحتاج مراجعة")

    if source is not None and source.requires_review:
        decision.status = ArticleStatus.review
        decision.reasons.append("المصدر يتطلب مراجعة تحريرية")

    if is_sensitive and rules["sensitive_requires_review"]:
        decision.status = ArticleStatus.review
        decision.reasons.append("محتوى حساس (ضحايا/عمليات/حالات طوارئ)")
        decision.verification_status = VerificationStatus.developing

    if is_breaking and rules["breaking_requires_review"]:
        decision.status = ArticleStatus.review
        decision.reasons.append("خبر عاجل يحتاج تأكيد التحرير")

    if source is not None and source.trust_tier > rules["min_source_trust"]:
        decision.status = ArticleStatus.review
        decision.reasons.append("مستوى ثقة المصدر غير كافٍ للنشر التلقائي")

    if category_slug and category_slug not in rules["auto_publish_categories"]:
        decision.status = ArticleStatus.review
        decision.reasons.append("القسم غير مدرج في النشر التلقائي")

    if rules["require_image"] and not has_image:
        decision.status = ArticleStatus.review
        decision.reasons.append("لا توجد صورة مرفقة")

    # If nothing forced a review, publish automatically when enabled.
    if decision.status == ArticleStatus.pending:
        if rules["auto_publish_enabled"]:
            decision.status = ArticleStatus.published
            decision.reasons.append("استوفى قواعد النشر التلقائي")
        else:
            decision.status = ArticleStatus.review
            decision.reasons.append("النشر التلقائي معطّل")

    return decision
