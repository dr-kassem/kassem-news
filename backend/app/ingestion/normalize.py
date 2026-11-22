"""Text normalization utilities tuned for Arabic news headlines."""
from __future__ import annotations

import hashlib
import html
import re
import unicodedata

_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL = "\u0640"
_PUNCT = re.compile(r"[^\w\s\u0600-\u06FF]", flags=re.UNICODE)
_WHITESPACE = re.compile(r"\s+")
_TAGS = re.compile(r"<[^>]+>")

# Common Arabic + English stopwords removed before fingerprinting.
_STOPWORDS = {
    "في", "من", "على", "الى", "إلى", "عن", "مع", "هذا", "هذه", "ذلك", "التي",
    "الذي", "بعد", "قبل", "بين", "خلال", "حول", "اي", "أي", "و", "او", "أو",
    "ثم", "قد", "كان", "قال", "قالت", "ان", "أن", "إن", "لا", "ما", "هو", "هي",
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are",
    "as", "at", "by", "with", "from", "that", "this", "it",
}


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(_TAGS.sub(" ", value))
    return _WHITESPACE.sub(" ", text).strip()


def normalize_arabic(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.replace(_TATWEEL, "")
    text = (
        text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        .replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
        .replace("ة", "ه")
    )
    text = text.lower()
    text = _PUNCT.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


def significant_tokens(text: str) -> list[str]:
    tokens = [t for t in normalize_arabic(text).split() if len(t) > 1]
    return [t for t in tokens if t not in _STOPWORDS]


def fingerprint(text: str) -> str:
    """Stable content fingerprint of a headline (order-insensitive)."""
    tokens = sorted(set(significant_tokens(text)))
    return hashlib.sha256(" ".join(tokens).encode("utf-8")).hexdigest()


def url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().lower().encode("utf-8")).hexdigest()


def truncate(text: str, limit: int = 320) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip() + "…"
