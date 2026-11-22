"""Seed reference data: regions, countries, categories, sources, rules, admin.

Run with:  python -m app.seed
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Category, Country, PublishingRule, Region, Role, Source, SourceType, User
from app.publishing import ensure_default_rules
from app.security import hash_password

logger = logging.getLogger("kassem.seed")

REGIONS = [
    {"slug": "lebanon", "name_ar": "لبنان", "name_en": "Lebanon"},
    {"slug": "middle-east", "name_ar": "الشرق الأوسط", "name_en": "Middle East"},
    {"slug": "world", "name_ar": "العالم", "name_en": "World"},
]

COUNTRIES = [
    ("LB", "لبنان", "Lebanon", "lebanon"),
    ("SY", "سوريا", "Syria", "middle-east"),
    ("IR", "إيران", "Iran", "middle-east"),
    ("IQ", "العراق", "Iraq", "middle-east"),
    ("PS", "فلسطين", "Palestine", "middle-east"),
    ("IL", "إسرائيل", "Israel", "middle-east"),
    ("SA", "السعودية", "Saudi Arabia", "middle-east"),
    ("AE", "الإمارات", "United Arab Emirates", "middle-east"),
    ("QA", "قطر", "Qatar", "middle-east"),
    ("EG", "مصر", "Egypt", "middle-east"),
    ("JO", "الأردن", "Jordan", "middle-east"),
    ("YE", "اليمن", "Yemen", "middle-east"),
    ("TR", "تركيا", "Turkey", "middle-east"),
    ("BH", "البحرين", "Bahrain", "middle-east"),
    ("KW", "الكويت", "Kuwait", "middle-east"),
    ("OM", "عُمان", "Oman", "middle-east"),
    ("LY", "ليبيا", "Libya", "world"),
    ("TN", "تونس", "Tunisia", "world"),
    ("DZ", "الجزائر", "Algeria", "world"),
    ("MA", "المغرب", "Morocco", "world"),
    ("SD", "السودان", "Sudan", "world"),
    ("US", "الولايات المتحدة", "United States", "world"),
    ("GB", "بريطانيا", "United Kingdom", "world"),
    ("FR", "فرنسا", "France", "world"),
    ("DE", "ألمانيا", "Germany", "world"),
    ("RU", "روسيا", "Russia", "world"),
    ("CN", "الصين", "China", "world"),
    ("UA", "أوكرانيا", "Ukraine", "world"),
]

CATEGORIES = [
    {"slug": "world", "name_ar": "العالم", "name_en": "World", "nav_order": 50},
    {"slug": "politics", "name_ar": "سياسة", "name_en": "Politics", "nav_order": 60},
    {"slug": "economy", "name_ar": "اقتصاد", "name_en": "Economy", "nav_order": 70},
    {"slug": "technology", "name_ar": "تكنولوجيا", "name_en": "Technology", "nav_order": 80},
    {"slug": "cybersecurity", "name_ar": "أمن سيبراني", "name_en": "Cybersecurity", "nav_order": 90},
    {"slug": "analysis", "name_ar": "تحليل وتحقيقات", "name_en": "Analysis", "nav_order": 100},
]

# Only feeds verified reachable and permitted for automated retrieval are enabled.
SOURCES = [
    {"slug": "bbc-arabic", "name_ar": "BBC عربي", "name_en": "BBC Arabic",
     "feed_url": "https://feeds.bbci.co.uk/arabic/rss.xml", "homepage": "https://www.bbc.com/arabic",
     "trust_tier": 1, "requires_review": False, "is_active": True,
     "rights_note": "خلاصة RSS عامة منشورة للاستخدام؛ نُعيد نشر الملخص والعنوان فقط مع الإحالة للمصدر."},
    {"slug": "aljazeera-ar", "name_ar": "الجزيرة نت", "name_en": "Al Jazeera Arabic",
     "feed_url": "https://www.aljazeera.net/rss", "homepage": "https://www.aljazeera.net",
     "trust_tier": 1, "requires_review": False, "is_active": True,
     "rights_note": "خلاصة RSS عامة؛ ملخصات مع إحالة أصلية."},
    {"slug": "france24-ar", "name_ar": "فرانس 24 عربي", "name_en": "France 24 Arabic",
     "feed_url": "https://www.france24.com/ar/rss", "homepage": "https://www.france24.com/ar",
     "trust_tier": 1, "requires_review": False, "is_active": True,
     "rights_note": "خلاصة RSS عامة؛ استرجاع آلي مسموح للعناوين والملخصات."},
    {"slug": "dw-ar", "name_ar": "DW عربية", "name_en": "DW Arabic",
     "feed_url": "https://rss.dw.com/xml/rss-ar-all", "homepage": "https://www.dw.com/ar",
     "trust_tier": 1, "requires_review": False, "is_active": True,
     "rights_note": "خلاصة RSS عامة من DW."},
    {"slug": "skynewsarabia", "name_ar": "سكاي نيوز عربية", "name_en": "Sky News Arabia",
     "feed_url": "https://www.skynewsarabia.com/rss", "homepage": "https://www.skynewsarabia.com",
     "trust_tier": 2, "requires_review": True, "is_active": True,
     "rights_note": "خلاصة RSS عامة؛ تُحوَّل للمراجعة التحريرية."},
    {"slug": "rt-arabic", "name_ar": "RT عربي", "name_en": "RT Arabic",
     "feed_url": "https://arabic.rt.com/rss/", "homepage": "https://arabic.rt.com",
     "trust_tier": 3, "requires_review": True, "is_active": True,
     "rights_note": "خلاصة RSS عامة؛ مصدر ذو موقف تحريري معروف ويخضع للمراجعة إلزامياً."},
    {"slug": "anadolu-ar", "name_ar": "وكالة أناضول", "name_en": "Anadolu Agency Arabic",
     "feed_url": "https://www.aa.com.tr/ar/rss/default?cat=guncel", "homepage": "https://www.aa.com.tr/ar",
     "trust_tier": 2, "requires_review": True, "is_active": True,
     "rights_note": "خلاصة RSS عامة من وكالة أناضول."},
    {"slug": "un-news-ar", "name_ar": "أخبار الأمم المتحدة", "name_en": "UN News Arabic",
     "feed_url": "https://news.un.org/feed/subscribe/ar/news/all/rss.xml",
     "homepage": "https://news.un.org/ar", "trust_tier": 1, "requires_review": False,
     "is_active": True, "rights_note": "خلاصة رسمية من الأمم المتحدة."},
    {"slug": "google-news-lb", "name_ar": "أخبار لبنان (Google News)", "name_en": "Google News Lebanon",
     "feed_url": "https://news.google.com/rss?hl=ar&gl=LB&ceid=LB:ar",
     "homepage": "https://news.google.com", "trust_tier": 2, "requires_review": True,
     "is_active": True, "rights_note": "مجمّع أخبار؛ يورَده رابط المصدر الأصلي ويخضع للمراجعة."},
    {"slug": "google-news-world", "name_ar": "أخبار العالم (Google News)", "name_en": "Google News World",
     "feed_url": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=ar&gl=LB&ceid=LB:ar",
     "homepage": "https://news.google.com", "trust_tier": 2, "requires_review": True,
     "is_active": True, "rights_note": "مجمّع أخبار عالمية بالعربية؛ يخضع للمراجعة."},
    {"slug": "google-news-me", "name_ar": "أخبار الشرق الأوسط (Google News)", "name_en": "Google News Middle East",
     "feed_url": "https://news.google.com/rss/search?q=%D8%A7%D9%84%D8%B4%D8%B1%D9%82+%D8%A7%D9%84%D8%A3%D9%88%D8%B3%D8%B7&hl=ar&gl=LB&ceid=LB:ar",
     "homepage": "https://news.google.com", "trust_tier": 2, "requires_review": True,
     "is_active": True, "rights_note": "بحث أخبار الشرق الأوسط؛ يخضع للمراجعة."},
    # --- Inactive by default: require licensed API or an explicit agreement ---
    {"slug": "reuters", "name_ar": "رويترز", "name_en": "Reuters",
     "feed_url": "", "homepage": "https://www.reuters.com", "trust_tier": 1,
     "requires_review": True, "is_active": False,
     "rights_note": "أوقفت رويترز خلاصات RSS العامة؛ يلزم اتفاق ترخيص/API تجاري لتفعيلها."},
    {"slug": "associated-press", "name_ar": "أسوشيتد برس", "name_en": "Associated Press",
     "feed_url": "", "homepage": "https://apnews.com", "trust_tier": 1,
     "requires_review": True, "is_active": False,
     "rights_note": "لا توفّر AP خلاصة RSS عامة؛ يلزم ترخيص محتوى معتمد."},
    {"slug": "alarabiya", "name_ar": "العربية", "name_en": "Al Arabiya",
     "feed_url": "https://www.alarabiya.net/feed/rss2/ar.xml", "homepage": "https://www.alarabiya.net",
     "trust_tier": 2, "requires_review": True, "is_active": False,
     "rights_note": "الخلاصة تُرجع 403 للوصول الآلي؛ تتطلب إذناً صريحاً قبل التفعيل."},
]


def seed(db: Session) -> None:
    region_ids: dict[str, int] = {}
    for data in REGIONS:
        region = db.scalar(select(Region).where(Region.slug == data["slug"]))
        if region is None:
            region = Region(**data)
            db.add(region)
            db.flush()
        region_ids[data["slug"]] = region.id

    for iso, ar, en, region_slug in COUNTRIES:
        if db.scalar(select(Country).where(Country.iso_code == iso)) is None:
            db.add(Country(iso_code=iso, name_ar=ar, name_en=en,
                           region_id=region_ids.get(region_slug)))

    for data in CATEGORIES:
        if db.scalar(select(Category).where(Category.slug == data["slug"])) is None:
            db.add(Category(**data))

    for data in SOURCES:
        if db.scalar(select(Source).where(Source.slug == data["slug"])) is None:
            db.add(Source(type=SourceType.rss, language="ar", **data))

    ensure_default_rules(db)

    if db.scalar(select(User).where(User.email == settings.admin_email)) is None:
        db.add(User(
            email=settings.admin_email,
            full_name=settings.admin_name,
            hashed_password=hash_password(settings.admin_password),
            role=Role.admin,
            is_active=True,
        ))

    db.commit()
    logger.info("seed complete")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        seed(db)
        print("تمت تهيئة البيانات المرجعية بنجاح.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
