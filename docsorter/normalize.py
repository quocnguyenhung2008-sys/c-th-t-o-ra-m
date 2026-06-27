from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
_LINEBREAK_RE = re.compile(r"\n{3,}")
_PUNCTUATION_REPLACEMENTS = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00a0": " ",
        "\u200b": "",
        "\ufeff": "",
    }
)

_OCR_REPLACEMENTS = (
    (re.compile(r"\b0(?=[a-zA-Z])"), "o"),
    (re.compile(r"(?<=[a-zA-Z])0\b"), "o"),
    (re.compile(r"\bl(?=\d)"), "1"),
    (re.compile(r"(?<=\d)l\b"), "1"),
)


@dataclass(frozen=True)
class NormalizedText:
    original: str
    normalized: str
    accentless: str


def strip_vietnamese_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


def normalize_text(text: str) -> NormalizedText:
    original = text or ""
    normalized = unicodedata.normalize("NFC", original)
    normalized = normalized.translate(_PUNCTUATION_REPLACEMENTS)
    normalized = normalized.lower()
    for pattern, replacement in _OCR_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    normalized = _LINEBREAK_RE.sub("\n\n", normalized).strip()
    accentless = strip_vietnamese_accents(normalized)
    return NormalizedText(original=original, normalized=normalized, accentless=accentless)
