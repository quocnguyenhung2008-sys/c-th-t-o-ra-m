from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .regex_utils import has_vietnamese_diacritics, keyword_to_accented_regex, keyword_to_regex


@dataclass(frozen=True)
class KeywordRule:
    subject: str
    keyword: str
    weight: float
    pattern: object
    accented_pattern: object
    has_diacritics: bool


@dataclass(frozen=True)
class NegativeRule:
    label: str
    keyword: str
    weight: float
    pattern: object
    accented_pattern: object
    has_diacritics: bool


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_keyword_rules(path: Path) -> list[KeywordRule]:
    raw = _load_json(path)
    rules: list[KeywordRule] = []
    for subject, entries in raw.items():
        for entry in entries:
            keyword = str(entry["keyword"])
            rules.append(
                KeywordRule(
                    subject=subject,
                    keyword=keyword,
                    weight=float(entry["weight"]),
                    pattern=keyword_to_regex(keyword),
                    accented_pattern=keyword_to_accented_regex(keyword),
                    has_diacritics=has_vietnamese_diacritics(keyword),
                )
            )
    return rules


def load_negative_rules(path: Path) -> list[NegativeRule]:
    raw = _load_json(path)
    rules: list[NegativeRule] = []
    for label, entries in raw.items():
        for entry in entries:
            keyword = str(entry["keyword"])
            rules.append(
                NegativeRule(
                    label=label,
                    keyword=keyword,
                    weight=float(entry["weight"]),
                    pattern=keyword_to_regex(keyword),
                    accented_pattern=keyword_to_accented_regex(keyword),
                    has_diacritics=has_vietnamese_diacritics(keyword),
                )
            )
    return rules


def load_aliases(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    raw = _load_json(path)
    if all(isinstance(value, list) for value in raw.values()):
        aliases: dict[str, str] = {}
        for subject, values in raw.items():
            for alias in values:
                aliases[str(alias)] = str(subject)
        return aliases
    return {str(alias): str(subject) for alias, subject in raw.items()}


def load_alias_rules(path: Path, weight: float) -> list[KeywordRule]:
    aliases = load_aliases(path)
    return [
        KeywordRule(
            subject=subject,
            keyword=alias,
            weight=weight,
            pattern=keyword_to_regex(alias),
            accented_pattern=keyword_to_accented_regex(alias),
            has_diacritics=has_vietnamese_diacritics(alias),
        )
        for alias, subject in aliases.items()
    ]


def subjects_from_rules(rules: Iterable[KeywordRule]) -> list[str]:
    return sorted({rule.subject for rule in rules})
