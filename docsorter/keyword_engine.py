from __future__ import annotations

import json
import re
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


def _optimize_pattern_boundaries(keyword: str, base_pattern: object) -> object:
    """
    Tối ưu hóa Regex Boundary dựa trên độ dài và bản chất của từ khóa.
    Giúp ngăn chặn lỗi nhận diện nhầm như: 'Van 12.pdf' (Đúng) vs 'Pham Van Trong.pdf' (Sai)
    """
    if not isinstance(base_pattern, re.Pattern):
        return base_pattern
        
    pattern_str = base_pattern.pattern
    
    # Nếu từ khóa quá ngắn (dưới 4 ký tự - thường là từ viết tắt như TA, Sử, Tin, Anh, Văn)
    # Ép buộc sử dụng ranh giới từ cứng để chống dính chữ trong chuỗi dài
    if len(keyword) <= 3:
        # Nếu pattern chưa bọc word boundary, tiến hành bọc chặt lại
        if not pattern_str.startswith(r'\b'):
            pattern_str = r'\b' + pattern_str
        if not pattern_str.endswith(r'\b'):
            pattern_str = pattern_str + r'\b'
            
    return re.compile(pattern_str, base_pattern.flags)


def load_keyword_rules(path: Path) -> list[KeywordRule]:
    raw = _load_json(path)
    rules: list[KeywordRule] = []
    seen_keywords: set[tuple[str, str]] = set()  # (subject, keyword) chặn trùng lặp

    for subject, entries in raw.items():
        for entry in entries:
            keyword = str(entry["keyword"]).strip().lower()
            if not keyword or (subject, keyword) in seen_keywords:
                continue
                
            seen_keywords.add((subject, keyword))
            
            # Khởi tạo Regex gốc
            raw_pattern = keyword_to_regex(keyword)
            raw_accented_pattern = keyword_to_accented_regex(keyword)
            
            # Áp dụng bộ lọc Boundary thông minh chống nhận diện sai
            final_pattern = _optimize_pattern_boundaries(keyword, raw_pattern)
            final_accented_pattern = _optimize_pattern_boundaries(keyword, raw_accented_pattern)

            rules.append(
                KeywordRule(
                    subject=subject,
                    keyword=keyword,
                    weight=float(entry["weight"]),
                    pattern=final_pattern,
                    accented_pattern=final_accented_pattern,
                    has_diacritics=has_vietnamese_diacritics(keyword),
                )
            )
            
    # TỐI ƯU QUAN TRỌNG: Sắp xếp luật theo độ dài từ khóa giảm dần (Longest Match First)
    # Giúp từ khóa dài, có nghĩa bao quát hơn được khớp trước, tăng độ chính xác scoring
    rules.sort(key=lambda r: len(r.keyword), reverse=True)
    return rules


def load_negative_rules(path: Path) -> list[NegativeRule]:
    raw = _load_json(path)
    rules: list[NegativeRule] = []
    seen_negatives: set[tuple[str, str]] = set()

    for label, entries in raw.items():
        for entry in entries:
            keyword = str(entry["keyword"]).strip().lower()
            if not keyword or (label, keyword) in seen_negatives:
                continue
                
            seen_negatives.add((label, keyword))
            
            raw_pattern = keyword_to_regex(keyword)
            raw_accented_pattern = keyword_to_accented_regex(keyword)
            
            final_pattern = _optimize_pattern_boundaries(keyword, raw_pattern)
            final_accented_pattern = _optimize_pattern_boundaries(keyword, raw_accented_pattern)

            rules.append(
                NegativeRule(
                    label=label,
                    keyword=keyword,
                    weight=float(entry["weight"]),
                    pattern=final_pattern,
                    accented_pattern=final_accented_pattern,
                    has_diacritics=has_vietnamese_diacritics(keyword),
                )
            )
            
    rules.sort(key=lambda r: len(r.keyword), reverse=True)
    return rules


def load_aliases(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    raw = _load_json(path)
    aliases: dict[str, str] = {}
    
    if all(isinstance(value, list) for value in raw.values()):
        for subject, values in raw.items():
            for alias in values:
                cleaned_alias = str(alias).strip().lower()
                if cleaned_alias:
                    aliases[cleaned_alias] = str(subject)
        return aliases
        
    for alias, subject in raw.items():
        cleaned_alias = str(alias).strip().lower()
        if cleaned_alias:
            aliases[cleaned_alias] = str(subject)
    return aliases


def load_alias_rules(path: Path, weight: float) -> list[KeywordRule]:
    aliases = load_aliases(path)
    rules: list[KeywordRule] = []
    
    for alias, subject in aliases.items():
        raw_pattern = keyword_to_regex(alias)
        raw_accented_pattern = keyword_to_accented_regex(alias)
        
        # Vì Alias thường rất ngắn (Anh, Văn, Toán, Sử...), bắt buộc phải qua bộ lọc ranh giới từ
        final_pattern = _optimize_pattern_boundaries(alias, raw_pattern)
        final_accented_pattern = _optimize_pattern_boundaries(alias, raw_accented_pattern)
        
        rules.append(
            KeywordRule(
                subject=subject,
                keyword=alias,
                weight=weight,
                pattern=final_pattern,
                accented_pattern=final_accented_pattern,
                has_diacritics=has_vietnamese_diacritics(alias),
            )
        )
        
    rules.sort(key=lambda r: len(r.keyword), reverse=True)
    return rules


def subjects_from_rules(rules: Iterable[KeywordRule]) -> list[str]:
    return sorted({rule.subject for rule in rules})