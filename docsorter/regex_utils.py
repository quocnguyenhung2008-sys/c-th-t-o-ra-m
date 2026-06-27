from __future__ import annotations

import re

from .normalize import strip_vietnamese_accents


_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
_VIETNAMESE_DIACRITIC_RE = re.compile(
    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệ"
    r"ìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
    r"ùúủũụưừứửữựỳýỷỹỵđ"
    r"ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆ"
    r"ÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ"
    r"ÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]"
)


def keyword_to_regex(keyword: str) -> re.Pattern[str]:
    """Compile a robust regex for Vietnamese keywords and noisy OCR spacing."""
    return compile_keyword_regex(strip_vietnamese_accents(keyword.lower()))


def keyword_to_accented_regex(keyword: str) -> re.Pattern[str]:
    return compile_keyword_regex(keyword.lower())


def compile_keyword_regex(keyword: str) -> re.Pattern[str]:
    tokens = _TOKEN_RE.findall(keyword)
    if not tokens:
        return re.compile(r"a\Ab")
    separator = r"[\s\-_.,;:/\\(){}\[\]<>|]+"
    pattern = separator.join(re.escape(token) for token in tokens)
    return re.compile(rf"(?<!\w){pattern}(?!\w)", re.IGNORECASE | re.UNICODE)


def has_vietnamese_diacritics(text: str) -> bool:
    return bool(_VIETNAMESE_DIACRITIC_RE.search(text or ""))
