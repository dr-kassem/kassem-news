from datetime import datetime, timezone

from app.ingestion import fingerprint, normalize_arabic, significant_tokens, url_hash


def test_normalize_arabic_letters():
    assert normalize_arabic("أحمد أحمد أحمد") == "احمد احمد احمد"
    assert normalize_arabic("مؤسسة") == "موسسه"


def test_normalize_removes_diacritics_and_tatweel():
    assert "\u0650" not in normalize_arabic("فِي")
    assert normalize_arabic("الـــخبر") == "الخبر"


def test_significant_tokens_excludes_stopwords():
    tokens = significant_tokens("في لبنان بيروت الشرق الأوسط")
    assert "في" not in tokens
    assert "لبنان" in tokens


def test_fingerprint_is_order_insensitive():
    assert fingerprint("هجوم على الحدود في لبنان") == fingerprint("لبنان هجوم على الحدود في")


def test_url_hash_is_stable():
    assert url_hash("https://example.com/x") == url_hash("  https://example.com/x  ")