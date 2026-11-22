"""Rule-based classification of articles into category / region / country.

The classifier is intentionally transparent and dependency-free: it scores
keyword dictionaries, which makes behaviour predictable and easy to audit.
It is a first pass; editors can always reclassify in the dashboard.
"""
from __future__ import annotations

from app.ingestion import normalize_arabic
from app.models import Sensitivity

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "politics": [
        "سياسه", "انتخابات", "حكومه", "برلمان", "رئيس", "وزير", "دبلوماسيه",
        "مفاوضات", "اتفاق", "معاهده", "سفير", "ائتلاف", "معارضه", "تشكيله",
        "government", "election", "parliament", "minister", "diplomacy",
    ],
    "economy": [
        "اقتصاد", "تضخم", "اسعار", "دولار", "نفط", "اسواق", "بورصه", "بنك",
        "استثمار", "تجاره", "ميزانيه", "صادرات", "واردات", "بطاله", "نمو",
        "economy", "inflation", "market", "oil", "trade", "budget", "bank",
    ],
    "technology": [
        "تكنولوجيا", "تقنيه", "ذكاء اصطناعي", "هاتف", "تطبيق", "انترنت",
        "رقميه", "منصه", "شركه تقنيه", "روبوت", "شبكات", "chip", "ai",
        "technology", "smartphone", "app", "internet", "software",
    ],
    "cybersecurity": [
        "امن سيبراني", "اختراق", "قرصنه", "فديه", "برمجيات خبيثه", "ثغره",
        "تسريب بيانات", "هاكر", "تصيد", "هجوم الكتروني", "سايب",
        "cyber", "hack", "ransomware", "malware", "breach", "phishing",
    ],
    "analysis": [
        "تحليل", "تحقيق", "تقرير خاص", "راى", "مقابله", "قراءه", "معمق",
        "analysis", "investigation", "opinion", "explainer", "review",
    ],
}

REGION_KEYWORDS: dict[str, list[str]] = {
    "lebanon": [
        "لبنان", "لبناني", "بيروت", "الجنوب اللبناني", "طرابلس", "صيدا", "بعلبك",
        "الضاحيه", "حزب الله", "لبناني", "البقاع", "جبيل", "زحلة", "النبطيه",
        "lebanon", "beirut", "lebanese",
    ],
    "middle-east": [
        "الشرق الاوسط", "سوريا", "سوريه", "سوري", "ايران", "ايراني", "العراق",
        "عراقي", "عراقيه", "فلسطين", "فلسطيني", "غزه", "اسرائيل", "اسرائيلي",
        "السعوديه", "سعودي", "الامارات", "قطر", "مصر", "مصري", "الاردن", "اليمن",
        "يمني", "الحوثي", "الحوثيين", "انصار الله", "صنعاء", "تركيا", "تركي",
        "البحرين", "الكويت", "دمشق", "طهران", "بغداد", "القدس", "رفح", "حماس",
        "عمان", "الدوحه", "الخرطوم", "ليبيا", "تونس", "الجزائر", "المغرب",
        "السودان", "المقاومه العراقيه", "الحشد",
        "middle east", "syria", "syrian", "iran", "iraq", "palestine", "gaza", "israel",
    ],
    "world": [
        "دولي", "امريكا", "امريكيه", "واشنطن", "اوروبا", "اوروبيه", "روسيا",
        "الصين", "اوكرانيا", "فرنسا", "بريطانيا", "المانيا", "اليابان", "الهند",
        "بوتين", "ترامب", "الناتو",
        "world", "global", "america", "europe", "russia", "china", "ukraine",
    ],
}

COUNTRY_KEYWORDS: dict[str, list[str]] = {
    "LB": ["لبنان", "لبناني", "بيروت", "lebanon", "beirut"],
    "SY": ["سوريا", "سوريه", "سوري", "دمشق", "syria", "damascus"],
    "IR": ["ايران", "ايراني", "طهران", "iran", "tehran"],
    "IQ": ["العراق", "عراقي", "عراقيه", "بغداد", "iraq", "baghdad"],
    "PS": ["فلسطين", "فلسطيني", "فلسطينيه", "غزه", "رام الله", "palestine", "gaza"],
    "IL": ["اسرائيل", "اسرائيلي", "اسرائيليه", "تل ابيب", "israel", "tel aviv"],
    "SA": ["السعوديه", "سعودي", "الرياض", "saudi", "riyadh"],
    "AE": ["الامارات", "اماراتي", "دبي", "ابوظبي", "emirates", "dubai"],
    "QA": ["قطر", "قطري", "الدوحه", "qatar", "doha"],
    "EG": ["مصر", "مصري", "مصريه", "القاهره", "egypt", "cairo"],
    "JO": ["الاردن", "اردني", "jordan", "amman"],
    "YE": ["اليمن", "يمني", "صنعاء", "عدن", "yemen", "sanaa"],
    "TR": ["تركيا", "تركي", "تركيه", "انقره", "اسطنبول", "turkey", "ankara"],
}

SENSITIVITY_KEYWORDS = [
    "قتل", "قتيل", "قتلى", "ضحايا", "جرحى", "مقتل", "وفيات", "غاره", "غارات",
    "قصف", "اشتباك", "اشتباكات", "عمليه عسكريه", "انفجار", "هجوم", "تفجير",
    "اعتداء", "اصابات", "اعتقال", "خطف", "رهائن", "كارثه", "حريق هائل",
    "حاله طوارئ", "تحذير عاجل", "تهديد", "تصعيد", "مواجهات", "استهداف",
    "casualties", "killed", "strike", "airstrike", "explosion", "attack",
    "shooting", "war", "missile", "emergency",
]

BREAKING_KEYWORDS = ["عاجل", "breaking", "urgent", "الان", "لحظة"]

# Terms indicating a live strike/raid report (airstrikes, shelling, drones,
# missiles, bombings) used by the «الغارات» section. Deliberately excludes broad
# words like «طيران»/«أجواء» (match civil aviation) and political words like
# «اعتداء»/«عدوان» (match condemnation statements) to keep the feed exclusive.
STRIKE_KEYWORDS = [
    "غارة", "غارات", "قصف", "مدفعي", "مدفعية",
    "استهداف", "استهدافات", "استهدف", "استهدفت",
    "مسيرة", "مسيرات", "درون", "درونات", "طائرة مسيرة", "طائرات مسيرة",
    "صاروخ", "صواريخ", "صاروخي", "قذيفة", "قذائف", "قنبلة", "قنابل",
    "تفجير", "تفجيرات", "انفجار", "انفجارات", "نسف", "تمشيط",
    "مروحية", "مروحيات", "طيران حربي", "طائرات حربية", "حربية",
    "اعتراض", "دفاعات جوية", "سلاح الجو",
]

# Order matters: more specific first.
_CATEGORY_ORDER = ["cybersecurity", "technology", "economy", "politics", "analysis"]
_REGION_ORDER = ["lebanon", "middle-east", "world"]


def _norm_list(items: list[str]) -> list[str]:
    return [normalize_arabic(x) for x in items]


# Store keyword tables in normalized form so they compare cleanly against the
# normalized text (otherwise e.g. «راى» never matches «راي»).
CATEGORY_KEYWORDS = {slug: _norm_list(kws) for slug, kws in CATEGORY_KEYWORDS.items()}
REGION_KEYWORDS = {slug: _norm_list(kws) for slug, kws in REGION_KEYWORDS.items()}
COUNTRY_KEYWORDS = {iso: _norm_list(kws) for iso, kws in COUNTRY_KEYWORDS.items()}
SENSITIVITY_KEYWORDS = _norm_list(SENSITIVITY_KEYWORDS)
BREAKING_KEYWORDS = _norm_list(BREAKING_KEYWORDS)
STRIKE_KEYWORDS = _norm_list(STRIKE_KEYWORDS)


def _score(text: str, keywords: list[str]) -> int:
    """Count keyword hits in normalized text, token-based.

    Matching only against whole tokens (with a definite-article variant) avoids
    the false positives that bidirectional substring matching produced — e.g.
    the token «الي» (from «إلى») collapsing to a single letter and matching any
    keyword that happened to contain that letter.
    """
    words = text.split()
    stripped = [w[2:] if len(w) > 3 and w.startswith("ال") else w for w in words]
    variants = set(words) | set(stripped)
    stripped_text = " ".join(stripped)

    total = 0
    for kw in keywords:
        if " " in kw:
            if kw in text or kw in stripped_text:
                total += 1
            continue
        for w in variants:
            if w == kw:
                total += 1
                break
            if len(kw) >= 3 and len(w) >= 3 and (w.startswith(kw) or kw.startswith(w)):
                total += 1
                break
    return total


def detect_category(title: str, body: str = "") -> str:
    # Headline carries more weight.
    title_n = normalize_arabic(title)
    body_n = normalize_arabic(body)
    best, best_score = None, 0
    for slug in _CATEGORY_ORDER:
        score = _score(title_n, CATEGORY_KEYWORDS[slug]) * 3 + _score(
            body_n, CATEGORY_KEYWORDS[slug]
        )
        if score > best_score:
            best, best_score = slug, score
    return best or "world"


def detect_region(title: str, body: str = "") -> str | None:
    text = normalize_arabic(f"{title} {body}")
    best, best_score = None, 0
    for slug in _REGION_ORDER:
        score = _score(text, REGION_KEYWORDS[slug])
        if score > best_score:
            best, best_score = slug, score
    return best


def detect_country(title: str, body: str = "") -> str | None:
    text = normalize_arabic(f"{title} {body}")
    best, best_score = None, 0
    for iso, keywords in COUNTRY_KEYWORDS.items():
        score = _score(text, keywords)
        if score > best_score:
            best, best_score = iso, score
    return best


def detect_sensitivity(title: str, body: str = "") -> Sensitivity:
    text = normalize_arabic(f"{title} {body}")
    return Sensitivity.sensitive if _score(text, SENSITIVITY_KEYWORDS) > 0 else Sensitivity.normal


def is_breaking(title: str) -> bool:
    text = normalize_arabic(title)
    words = text.split()
    variants = set(words) | {w[2:] if len(w) > 3 and w.startswith("ال") else w for w in words}
    for kw in BREAKING_KEYWORDS:
        if " " in kw:
            if kw in text:
                return True
        elif kw in variants:
            return True
    return False


def is_strike(title: str, body: str = "") -> bool:
    """True when the headline reports a strike/raid (airstrike, shelling, drone,
    missile, bombing). Matched against the title only to keep the «الغارات»
    section focused and exclusive."""
    text = normalize_arabic(title)
    return any(kw in text for kw in STRIKE_KEYWORDS)
