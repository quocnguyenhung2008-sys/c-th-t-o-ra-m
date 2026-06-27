from __future__ import annotations

from dataclasses import dataclass, field

from .keyword_engine import KeywordRule, NegativeRule
from .normalize import normalize_text
from .regex_utils import has_vietnamese_diacritics

_SHORT_ALIAS_CONTEXT_WORDS = {
    "bai",
    "bo",
    "chuyen",
    "de",
    "decuong",
    "giao",
    "giaoan",
    "hk",
    "hki",
    "hkii",
    "hoc",
    "kiem",
    "ki",
    "ky",
    "lop",
    "mon",
    "on",
    "tap",
    "thi",
    "thpt",
    "tn",
    "tot",
    "tra",
}

_GRADE_TOKENS = {"10", "11", "12"}
_RISKY_SINGLE_TOKENS = {
    "ai",
    "anh",
    "hoa",
    "ly",
    "su",
    "ta",
    "tin",
    "tuong",
    "van",
    "vo",
}


@dataclass(frozen=True)
class MatchEvidence:
    keyword: str
    count: int
    score: float
    source: str


@dataclass
class SubjectScore:
    subject: str
    score: float = 0.0
    evidence: list[MatchEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class ScoreResult:
    scores: dict[str, SubjectScore]
    negative_score: float
    negative_evidence: list[MatchEvidence]


def _score_rules(
    rules: list[KeywordRule],
    text: str,
    source: str,
    multiplier: float,
    scores: dict[str, SubjectScore],
) -> None:
    text_forms = normalize_text(text)
    text_has_diacritics = has_vietnamese_diacritics(text_forms.normalized)
    for rule in rules:
        matches = _find_rule_matches(rule, text_forms.normalized, text_forms.accentless, text_has_diacritics)
        for match_source, match_count in matches:
            if not match_count:
                continue
            score = match_count * rule.weight * multiplier
            subject_score = scores.setdefault(rule.subject, SubjectScore(subject=rule.subject))
            subject_score.score += score
            subject_score.evidence.append(
                MatchEvidence(keyword=rule.keyword, count=match_count, score=score, source=f"{source}:{match_source}")
            )


def _find_rule_matches(
    rule: KeywordRule,
    normalized_text: str,
    accentless_text: str,
    text_has_diacritics: bool,
) -> list[tuple[str, int]]:
    accented_count = 0
    if rule.has_diacritics and text_has_diacritics:
        accented_count = len(list(rule.accented_pattern.finditer(normalized_text)))
        if accented_count:
            return [("accented", accented_count)]

    if _should_skip_accentless_fallback(rule, text_has_diacritics):
        return []
    accentless_count = len(list(rule.pattern.finditer(accentless_text)))
    return [("accentless", accentless_count)] if accentless_count else []


def _should_skip_accentless_fallback(rule: KeywordRule, text_has_diacritics: bool) -> bool:
    if not text_has_diacritics:
        return False
    keyword = normalize_text(rule.keyword).accentless.strip()
    if len(keyword.split()) > 1:
        return False
    return keyword in _RISKY_SINGLE_TOKENS


def _score_filename_alias_rules(
    rules: list[KeywordRule],
    filename_text: str,
    multiplier: float,
    scores: dict[str, SubjectScore],
) -> None:
    text_forms = normalize_text(filename_text)
    text_has_diacritics = has_vietnamese_diacritics(text_forms.normalized)
    tokens = text_forms.accentless.split()
    for rule in rules:
        if _is_unsafe_short_alias(rule.keyword) and not _short_alias_allowed(tokens, rule.keyword):
            continue
        matches = _find_rule_matches(rule, text_forms.normalized, text_forms.accentless, text_has_diacritics)
        for match_source, match_count in matches:
            if not match_count:
                continue
            score = match_count * rule.weight * multiplier
            subject_score = scores.setdefault(rule.subject, SubjectScore(subject=rule.subject))
            subject_score.score += score
            subject_score.evidence.append(
                MatchEvidence(keyword=rule.keyword, count=match_count, score=score, source=f"filename_alias:{match_source}")
            )


def _is_unsafe_short_alias(alias: str) -> bool:
    normalized_alias = normalize_text(alias).accentless.strip()
    return len(normalized_alias.split()) == 1 and normalized_alias in _RISKY_SINGLE_TOKENS


def _short_alias_allowed(tokens: list[str], alias: str) -> bool:
    normalized_alias = normalize_text(alias).accentless.strip()
    if tokens == [normalized_alias]:
        return True
    if len(tokens) == 2 and normalized_alias in tokens and any(token in _GRADE_TOKENS for token in tokens):
        return True
    for index, token in enumerate(tokens):
        if token != normalized_alias:
            continue
        previous_token = tokens[index - 1] if index > 0 else ""
        next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
        if previous_token in _SHORT_ALIAS_CONTEXT_WORDS or next_token in _SHORT_ALIAS_CONTEXT_WORDS:
            return True
        if next_token in _GRADE_TOKENS:
            return True
    return False


def _score_negative_rules(
    rules: list[NegativeRule],
    text: str,
    source: str,
    multiplier: float,
) -> tuple[float, list[MatchEvidence]]:
    text_forms = normalize_text(text)
    text_has_diacritics = has_vietnamese_diacritics(text_forms.normalized)
    total = 0.0
    evidence: list[MatchEvidence] = []
    for rule in rules:
        accented_count = 0
        if rule.has_diacritics and text_has_diacritics:
            accented_count = len(list(rule.accented_pattern.finditer(text_forms.normalized)))
        count = accented_count or len(list(rule.pattern.finditer(text_forms.accentless)))
        if not count:
            continue
        score = count * rule.weight * multiplier
        total += score
        evidence.append(MatchEvidence(keyword=rule.keyword, count=count, score=score, source=source))
    return total, evidence


def score_document(
    filename_text: str,
    body_text: str,
    keyword_rules: list[KeywordRule],
    negative_rules: list[NegativeRule],
    filename_multiplier: float,
    body_multiplier: float,
    filename_alias_rules: list[KeywordRule] | None = None,
) -> ScoreResult:
    scores: dict[str, SubjectScore] = {}
    _score_rules(keyword_rules, filename_text, "filename", filename_multiplier, scores)
    if filename_alias_rules:
        _score_filename_alias_rules(filename_alias_rules, filename_text, filename_multiplier, scores)
    _score_rules(keyword_rules, body_text, "body", body_multiplier, scores)

    filename_negative, filename_evidence = _score_negative_rules(
        negative_rules, filename_text, "filename", filename_multiplier
    )
    body_negative, body_evidence = _score_negative_rules(negative_rules, body_text, "body", body_multiplier)
    return ScoreResult(
        scores=scores,
        negative_score=filename_negative + body_negative,
        negative_evidence=filename_evidence + body_evidence,
    )
