from __future__ import annotations

from dataclasses import dataclass, field

from .keyword_engine import KeywordRule, NegativeRule
from .normalize import normalize_text
from .regex_utils import has_vietnamese_diacritics

# MỞ RỘNG: Bổ sung thêm các từ ngữ cảnh giúp nhận diện chính xác alias ngắn trong THPT
_SHORT_ALIAS_CONTEXT_WORDS = {
    "bai", "bo", "chuyen", "de", "decuong", "giao", "giaoan",
    "hk", "hki", "hkii", "hoc", "kiem", "ki", "ky", "lop", "mon",
    "on", "tap", "thi", "thpt", "tn", "tot", "tra",
    "khao", "sat", "tuyen", "sinh", "chuyen", "boiduong", "hsg"
}

_GRADE_TOKENS = {"10", "11", "12"}
_RISKY_SINGLE_TOKENS = {
    "ai", "anh", "hoa", "ly", "li", "su", "ta", "tin", "toan", "tuong", "van", "vo",
}

# Tiền tố thư mục cho nhãn negative — giúp các thư mục nhóm lại đầu danh sách
_LABEL_PREFIX = "_"


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
    # Nhãn thư mục của nhóm negative thắng (nếu có), ví dụ "_Hop_dong"
    winning_negative_label: str = ""


def _score_rules(
    rules: list[KeywordRule],
    text: str,
    source: str,
    multiplier: float,
    scores: dict[str, SubjectScore],
) -> None:
    text_forms = normalize_text(text)
    text_has_diacritics = has_vietnamese_diacritics(text_forms.normalized)
    accentless_tokens = text_forms.accentless.split()
    for rule in rules:
        if _is_unsafe_short_alias(rule.keyword):
            if source == "filename" and not _short_alias_allowed(accentless_tokens, rule.keyword):
                continue
            if source == "body":
                continue
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
) -> tuple[float, list[MatchEvidence], dict[str, float]]:
    """
    Trả về:
      - tổng điểm negative
      - danh sách evidence
      - dict {label -> tổng điểm} để xác định nhóm thắng
    """
    text_forms = normalize_text(text)
    text_has_diacritics = has_vietnamese_diacritics(text_forms.normalized)
    total = 0.0
    evidence: list[MatchEvidence] = []
    label_scores: dict[str, float] = {}

    for rule in rules:
        accented_count = 0
        if rule.has_diacritics and text_has_diacritics:
            accented_count = len(list(rule.accented_pattern.finditer(text_forms.normalized)))
        count = accented_count or len(list(rule.pattern.finditer(text_forms.accentless)))
        if not count:
            continue
        score = count * rule.weight * multiplier
        total += score
        label_scores[rule.label] = label_scores.get(rule.label, 0.0) + score
        evidence.append(MatchEvidence(keyword=rule.keyword, count=count, score=score, source=source))

    return total, evidence, label_scores


def _resolve_winning_label(
    filename_label_scores: dict[str, float],
    body_label_scores: dict[str, float],
) -> str:
    """Cộng điểm từng nhóm (filename + body) rồi chọn nhóm có điểm cao nhất."""
    merged: dict[str, float] = {}
    for label, score in {**filename_label_scores, **body_label_scores}.items():
        merged[label] = merged.get(label, 0.0) + score
    if not merged:
        return ""
    winning = max(merged, key=lambda k: merged[k])
    # Thêm tiền tố _ nếu chưa có để tạo thư mục _Hop_dong, _Hoc_sinh_gioi, ...
    return winning if winning.startswith(_LABEL_PREFIX) else f"{_LABEL_PREFIX}{winning}"


def score_document(
    filename_text: str,
    body_text: str,
    keyword_rules: list[KeywordRule],
    negative_rules: list[NegativeRule],
    filename_multiplier: float,
    body_multiplier: float,
    filename_alias_rules: list[KeywordRule] | None = None,
) -> ScoreResult:
    """
    Tính toán điểm tài liệu và thực thi bộ lọc gạt giò (Veto)
    để loại bỏ các văn bản hành chính/phi môn học ra khỏi danh mục môn học.
    Nhãn thư mục đích được suy ra từ nhóm negative thắng (Hop_dong, Hoc_sinh_gioi, Hanh_chinh...).
    """
    scores: dict[str, SubjectScore] = {}

    # 1. Chấm điểm từ khóa môn học
    _score_rules(keyword_rules, filename_text, "filename", filename_multiplier, scores)
    if filename_alias_rules:
        _score_filename_alias_rules(filename_alias_rules, filename_text, filename_multiplier, scores)
    _score_rules(keyword_rules, body_text, "body", body_multiplier, scores)

    # 2. Chấm điểm từ khóa tiêu cực — tách riêng filename và body để cộng label_scores
    filename_neg_total, filename_neg_evidence, filename_label_scores = _score_negative_rules(
        negative_rules, filename_text, "filename", filename_multiplier
    )
    body_neg_total, body_neg_evidence, body_label_scores = _score_negative_rules(
        negative_rules, body_text, "body", body_multiplier
    )

    total_negative_score = filename_neg_total + body_neg_total
    total_negative_evidence = filename_neg_evidence + body_neg_evidence

    # Xác định nhóm negative thắng để dùng làm nhãn thư mục
    winning_label = _resolve_winning_label(filename_label_scores, body_label_scores)

    # =========================================================================
    # 🔥 BỘ LỌC CẢN PHÁN QUYẾT (VETO MECHANISM) — giữ nguyên logic cũ
    # =========================================================================
    is_strong_administrative = any(ev.score >= 40.0 for ev in total_negative_evidence)

    if is_strong_administrative:
        # Dùng winning_label thay vì hardcode _Khong_phai_mon_hoc
        veto_label = winning_label or "_Khong_phai_mon_hoc"
        veto_score = SubjectScore(subject=veto_label, score=999.0)
        veto_score.evidence = total_negative_evidence
        return ScoreResult(
            scores={veto_label: veto_score},
            negative_score=total_negative_score,
            negative_evidence=total_negative_evidence,
            winning_negative_label=veto_label,
        )

    # Khấu trừ điểm phạt tuyến tính cho các trường hợp negative nhẹ
    if total_negative_score > 0 and scores:
        filtered_scores: dict[str, SubjectScore] = {}
        for subj, subj_score in scores.items():
            adjusted_score = subj_score.score - total_negative_score
            if adjusted_score > 10.0:
                subj_score.score = adjusted_score
                filtered_scores[subj] = subj_score
        scores = filtered_scores

    return ScoreResult(
        scores=scores,
        negative_score=total_negative_score,
        negative_evidence=total_negative_evidence,
        winning_negative_label=winning_label,
    )