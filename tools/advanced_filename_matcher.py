#!/usr/bin/env python3
"""Phan tich va toi uu filename matcher cho classification_report.csv.

Muc tieu:
- Tim cac keyword/alias khong dau gay nhieu trong report cu.
- Phan loai lai filename bang matcher phan tang:
  1. Filename co dau: uu tien keyword co dau.
  2. Filename khong dau: dung keyword khong dau, nhung ap dung context gate
     cho token ngan/de nhieu nhu van, ly, hoa, tin, su, tuong.
- Xuat bang doi chieu old label vs new label va danh sach file bi doi nhan.

Chay mac dinh:
    python3 tools/advanced_filename_matcher.py

Chay voi duong dan tuy chinh:
    python3 tools/advanced_filename_matcher.py \
      --report "/Users/billcipher/Documents/PhanLoai/classification_report.csv"
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = Path("/Users/billcipher/Documents/PhanLoai/classification_report.csv")
DEFAULT_KEYWORDS = PROJECT_ROOT / "data" / "keywords.json"
DEFAULT_ALIASES = PROJECT_ROOT / "data" / "aliases.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "filename_matcher_analysis"

UNCERTAIN_LABELS = {"_Can_kiem_tra", "_Khong_xac_dinh", "_Khong_phai_mon_hoc"}
ACTIVE_SUBJECTS = {"Toan", "Vat_ly", "Hoa_hoc", "Sinh_hoc", "Ngu_van", "Lich_su", "Tieng_Anh", "Tin_hoc"}

RISKY_SINGLE_TOKENS = {
    "anh",
    "av",
    "hoa",
    "ly",
    "su",
    "ta",
    "tin",
    "van",
    "tuong",
}

FILENAME_CONTEXT_TOKENS = {
    "bai",
    "bo",
    "bt",
    "chu de",
    "chuong",
    "chuyen de",
    "de",
    "de cuong",
    "giao an",
    "hk",
    "hki",
    "hkii",
    "hoc",
    "kiem tra",
    "lop",
    "mon",
    "on",
    "phan",
    "sach",
    "sgk",
    "tai lieu",
    "tap",
    "thi",
    "thpt",
    "trac nghiem",
}

GRADE_TOKENS = {"10", "11", "12"}


@dataclass(frozen=True)
class KeywordRule:
    subject: str
    keyword: str
    normalized_keyword: str
    weight: float
    layer: str
    risky: bool
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class MatchEvidence:
    subject: str
    keyword: str
    layer: str
    count: int
    score: float


@dataclass(frozen=True)
class Prediction:
    label: str
    status: str
    score: float
    runner_up_score: float
    evidence: tuple[MatchEvidence, ...]
    used_layer: str


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", str(text or ""))


def strip_vietnamese_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


def normalize_for_matching(text: str, *, keep_accents: bool) -> str:
    text = normalize_unicode(text).lower()
    if not keep_accents:
        text = strip_vietnamese_accents(text)
    text = text.translate(
        str.maketrans(
            {
                "\u00a0": " ",
                "\u200b": "",
                "\ufeff": "",
                "_": " ",
                "-": " ",
                ".": " ",
                ",": " ",
                "(": " ",
                ")": " ",
                "[": " ",
                "]": " ",
                "{": " ",
                "}": " ",
            }
        )
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text


def filename_from_source(source: str) -> str:
    return Path(str(source)).stem


def has_vietnamese_diacritics(text: str) -> bool:
    normalized = normalize_unicode(text)
    return strip_vietnamese_accents(normalized).lower() != normalized.lower()


def token_count(text: str) -> int:
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def compile_keyword_regex(keyword: str) -> re.Pattern[str]:
    tokens = re.findall(r"\w+", keyword, flags=re.UNICODE)
    if not tokens:
        return re.compile(r"a\Ab")
    separator = r"[\s\-_.,;:/\\(){}\[\]<>|]+"
    pattern = separator.join(re.escape(token) for token in tokens)
    return re.compile(rf"(?<!\w){pattern}(?!\w)", re.IGNORECASE | re.UNICODE)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def iter_aliases(path: Path) -> Iterable[tuple[str, str]]:
    raw = load_json(path)
    if all(isinstance(value, list) for value in raw.values()):
        for subject, aliases in raw.items():
            for alias in aliases:
                yield subject, str(alias)
    else:
        for alias, subject in raw.items():
            yield str(subject), str(alias)


def build_rule_set(keywords_path: Path, aliases_path: Path) -> list[KeywordRule]:
    rules: list[KeywordRule] = []

    # Cac cum co dau dac trung, dung lam tang uu tien khi filename co dau.
    accented_seed_rules: dict[str, list[tuple[str, float]]] = {
        "Toan": [
            ("toán", 40),
            ("môn toán", 50),
            ("đại số", 34),
            ("hình học", 34),
            ("giải tích", 36),
            ("đạo hàm", 40),
            ("nguyên hàm", 40),
            ("tích phân", 40),
            ("xác suất", 34),
        ],
        "Vat_ly": [
            ("vật lý", 50),
            ("vật lí", 50),
            ("môn lý", 44),
            ("môn vật lý", 55),
            ("cơ học", 34),
            ("điện trường", 38),
            ("từ trường", 38),
            ("dao động điều hòa", 42),
        ],
        "Hoa_hoc": [
            ("hóa", 38),
            ("hoá", 38),
            ("hóa học", 55),
            ("hoá học", 55),
            ("môn hóa", 50),
            ("môn hoá", 50),
            ("este", 36),
            ("alcohol", 34),
            ("phenol", 34),
            ("phản ứng hóa học", 42),
        ],
        "Sinh_hoc": [
            ("sinh", 38),
            ("sinh học", 55),
            ("môn sinh", 50),
            ("tế bào", 36),
            ("di truyền", 40),
            ("nhiễm sắc thể", 42),
            ("quần thể sinh vật", 42),
        ],
        "Ngu_van": [
            ("văn", 34),
            ("ngữ văn", 55),
            ("môn văn", 50),
            ("văn học", 44),
            ("đọc hiểu", 38),
            ("nghị luận văn học", 44),
            ("tuồng", 46),
            ("nghệ thuật tuồng", 58),
            ("vở tuồng", 54),
            ("kịch tuồng", 54),
        ],
        "Lich_su": [
            ("sử", 34),
            ("lịch sử", 55),
            ("môn sử", 50),
            ("cách mạng tháng tám", 44),
            ("điện biên phủ", 44),
        ],
        "Tieng_Anh": [
            ("anh", 34),
            ("tiếng anh", 60),
            ("môn anh", 50),
            ("anh văn", 55),
            ("anh ngữ", 55),
            ("english", 50),
            ("ielts", 42),
            ("toeic", 42),
        ],
        "Tin_hoc": [
            ("tin", 34),
            ("tin học", 55),
            ("môn tin", 50),
            ("lập trình", 42),
            ("thuật toán", 42),
            ("cơ sở dữ liệu", 42),
            ("đối tượng", 20),
        ],
    }

    for subject, entries in accented_seed_rules.items():
        if subject not in ACTIVE_SUBJECTS:
            continue
        for keyword, weight in entries:
            rules.append(make_rule(subject, keyword, weight, layer="accented"))

    keyword_data = load_json(keywords_path)
    for subject, entries in keyword_data.items():
        if subject not in ACTIVE_SUBJECTS:
            continue
        for entry in entries:
            keyword = str(entry["keyword"])
            weight = float(entry["weight"])
            rules.append(make_rule(subject, keyword, weight, layer="accentless"))

    for subject, alias in iter_aliases(aliases_path):
        if subject not in ACTIVE_SUBJECTS:
            continue
        base_weight = 36.0 if token_count(alias) == 1 else 46.0
        rules.append(make_rule(subject, alias, base_weight, layer="accentless"))

    contextual_rules = [
        ("Hoa_hoc", "ester", 44),
        ("Hoa_hoc", "alcohol", 44),
        ("Hoa_hoc", "phenol", 44),
        ("Hoa_hoc", "carbonyl", 44),
        ("Hoa_hoc", "carboxylic acid", 52),
        ("Hoa_hoc", "aldehyde", 44),
        ("Hoa_hoc", "ketone", 44),
        ("Hoa_hoc", "alkane", 40),
        ("Hoa_hoc", "alkene", 40),
        ("Hoa_hoc", "alkyne", 40),
        ("Toan", "oxyz", 42),
        ("Toan", "he phuong trinh", 44),
        ("Vat_ly", "luc tu", 40),
        ("Vat_ly", "phong xa", 42),
        ("Lich_su", "thuc dan phap", 44),
        ("Ngu_van", "nghe thuat tuong", 64),
        ("Ngu_van", "vo tuong", 60),
        ("Ngu_van", "kich tuong", 60),
        ("Ngu_van", "san khau tuong", 60),
        ("Vat_ly", "luc tuong tac", 52),
        ("Vat_ly", "tuong tac dien", 52),
        ("Vat_ly", "tuong tac tu", 52),
        ("Tin_hoc", "doi tuong", 44),
        ("Tin_hoc", "lap trinh huong doi tuong", 60),
        ("Lich_su", "tuong dai", 28),
    ]
    for subject, keyword, weight in contextual_rules:
        rules.append(make_rule(subject, keyword, weight, layer="accentless"))

    rules.sort(key=lambda rule: (token_count(rule.normalized_keyword), rule.weight), reverse=True)
    return deduplicate_rules(rules)


def make_rule(subject: str, keyword: str, weight: float, layer: str) -> KeywordRule:
    keep_accents = layer == "accented"
    normalized_keyword = normalize_for_matching(keyword, keep_accents=keep_accents)
    risky = token_count(normalized_keyword) == 1 and strip_vietnamese_accents(normalized_keyword) in RISKY_SINGLE_TOKENS
    return KeywordRule(
        subject=subject,
        keyword=keyword,
        normalized_keyword=normalized_keyword,
        weight=weight,
        layer=layer,
        risky=risky,
        pattern=compile_keyword_regex(normalized_keyword),
    )


def deduplicate_rules(rules: list[KeywordRule]) -> list[KeywordRule]:
    best: dict[tuple[str, str, str], KeywordRule] = {}
    for rule in rules:
        key = (rule.subject, rule.normalized_keyword, rule.layer)
        if key not in best or rule.weight > best[key].weight:
            best[key] = rule
    return list(best.values())


def has_context(normalized_filename: str, keyword: str) -> bool:
    tokens = normalized_filename.split()
    keyword_tokens = keyword.split()
    if len(keyword_tokens) != 1:
        return True
    token = keyword_tokens[0]

    if tokens == [token]:
        return True
    if len(tokens) == 2 and token in tokens and any(item in GRADE_TOKENS for item in tokens):
        return True

    context_phrases = set(FILENAME_CONTEXT_TOKENS)
    for index, item in enumerate(tokens):
        if item != token:
            continue
        previous_token = tokens[index - 1] if index > 0 else ""
        next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
        if previous_token in context_phrases or next_token in context_phrases:
            return True
        if previous_token in GRADE_TOKENS or next_token in GRADE_TOKENS:
            return True
        previous_bigram = " ".join(tokens[max(0, index - 2) : index])
        next_bigram = " ".join(tokens[index + 1 : index + 3])
        if previous_bigram in context_phrases or next_bigram in context_phrases:
            return True

    return False


def predict_filename(filename: str, rules: list[KeywordRule], min_score: float = 18.0, min_margin: float = 8.0) -> Prediction:
    accented_filename = normalize_for_matching(filename, keep_accents=True)
    accentless_filename = normalize_for_matching(filename, keep_accents=False)
    filename_has_diacritics = has_vietnamese_diacritics(filename)

    if filename_has_diacritics:
        accented_prediction = score_layer(accented_filename, rules, layer="accented", min_score=min_score, min_margin=min_margin)
        if accented_prediction.status == "subject":
            return accented_prediction

    return score_layer(accentless_filename, rules, layer="accentless", min_score=min_score, min_margin=min_margin)


def score_layer(normalized_filename: str, rules: list[KeywordRule], layer: str, min_score: float, min_margin: float) -> Prediction:
    scores: dict[str, float] = defaultdict(float)
    evidence_by_subject: dict[str, list[MatchEvidence]] = defaultdict(list)

    for rule in rules:
        if rule.layer != layer:
            continue
        if rule.risky and not has_context(normalized_filename, rule.normalized_keyword):
            continue
        matches = list(rule.pattern.finditer(normalized_filename))
        if not matches:
            continue
        phrase_bonus = 1.0 + min(token_count(rule.normalized_keyword) - 1, 4) * 0.18
        score = len(matches) * rule.weight * phrase_bonus
        scores[rule.subject] += score
        evidence_by_subject[rule.subject].append(
            MatchEvidence(rule.subject, rule.keyword, layer, len(matches), score)
        )

    if not scores:
        return Prediction("_Khong_xac_dinh", "unknown", 0.0, 0.0, tuple(), layer)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    label, score = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
    evidence = tuple(sorted(evidence_by_subject[label], key=lambda item: item.score, reverse=True))

    if score < min_score:
        return Prediction("_Khong_xac_dinh", "unknown", score, runner_up, evidence, layer)
    if runner_up > 0 and score - runner_up < min_margin:
        return Prediction("_Can_kiem_tra", "conflict", score, runner_up, evidence, layer)
    return Prediction(label, "subject", score, runner_up, evidence, layer)


def extract_old_keywords(top_evidence: str) -> list[str]:
    if not isinstance(top_evidence, str):
        return []
    keywords = []
    for chunk in top_evidence.split(";"):
        chunk = chunk.strip()
        match = re.match(r"[^:]+:(.*?)\s+x\d+=", chunk)
        if match:
            keywords.append(normalize_for_matching(match.group(1), keep_accents=False))
    return keywords


def analyze_noisy_tokens(df: pd.DataFrame) -> pd.DataFrame:
    filename_df = df[df["engine"].fillna("") == "filename"].copy()
    suspicious = filename_df[
        filename_df["label"].isin(UNCERTAIN_LABELS)
        | filename_df["top_evidence"].fillna("").str.contains("|".join(RISKY_SINGLE_TOKENS), case=False, regex=True)
    ].copy()

    counter: Counter[str] = Counter()
    for evidence in suspicious["top_evidence"].fillna(""):
        for keyword in extract_old_keywords(evidence):
            for token in keyword.split():
                if len(token) >= 2:
                    counter[token] += 1

    rows = [{"token": token, "count": count} for token, count in counter.most_common(100)]
    return pd.DataFrame(rows)


def build_comparison(df: pd.DataFrame, rules: list[KeywordRule]) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        source = row.get("source", "")
        filename = filename_from_source(source)
        prediction = predict_filename(filename, rules)
        evidence_text = "; ".join(
            f"{item.layer}:{item.keyword} x{item.count}={item.score:.1f}" for item in prediction.evidence[:8]
        )
        rows.append(
            {
                "source": source,
                "filename": filename,
                "old_label": row.get("label", ""),
                "old_status": row.get("status", ""),
                "old_engine": row.get("engine", ""),
                "old_score": row.get("score", 0),
                "old_evidence": row.get("top_evidence", ""),
                "new_label": prediction.label,
                "new_status": prediction.status,
                "new_score": round(prediction.score, 2),
                "new_runner_up_score": round(prediction.runner_up_score, 2),
                "new_layer": prediction.used_layer,
                "new_evidence": evidence_text,
                "changed": row.get("label", "") != prediction.label,
            }
        )
    return pd.DataFrame(rows)


def print_evaluation(comparison: pd.DataFrame) -> None:
    filename_only = comparison[comparison["old_engine"] == "filename"].copy()
    if filename_only.empty:
        print("Khong co dong nao dung engine=filename.")
        return

    old_uncertain_rate = filename_only["old_label"].isin(UNCERTAIN_LABELS).mean()
    new_uncertain_rate = filename_only["new_label"].isin(UNCERTAIN_LABELS).mean()
    changed_rate = filename_only["changed"].mean()

    print("\n=== Tong quan engine=filename ===")
    print(f"So dong filename: {len(filename_only):,}")
    print(f"Ti le nhan cu khong chac chan: {old_uncertain_rate:.2%}")
    print(f"Ti le nhan moi khong chac chan: {new_uncertain_rate:.2%}")
    print(f"Ti le dong doi nhan: {changed_rate:.2%}")

    print("\n=== Bang doi chieu old_label vs new_label ===")
    matrix = pd.crosstab(filename_only["old_label"], filename_only["new_label"], dropna=False)
    print(matrix.to_string())

    improved = filename_only[
        filename_only["old_label"].isin(UNCERTAIN_LABELS) & ~filename_only["new_label"].isin(UNCERTAIN_LABELS)
    ]
    safer = filename_only[
        ~filename_only["old_label"].isin(UNCERTAIN_LABELS) & filename_only["new_label"].isin(UNCERTAIN_LABELS)
    ]
    print("\n=== Uoc tinh cai thien ===")
    print(f"Tu khong chac chan -> co nhan mon: {len(improved):,}")
    print(f"Tu co nhan mon -> can xem lai/khong xac dinh: {len(safer):,}")
    print("Luu y: neu khong co cot ground truth, day la doi chieu heuristic, khong phai accuracy that.")


def maybe_print_ground_truth_metrics(comparison: pd.DataFrame, ground_truth_column: str | None) -> None:
    if not ground_truth_column or ground_truth_column not in comparison.columns:
        return
    valid = comparison[comparison[ground_truth_column].notna()].copy()
    if valid.empty:
        return
    old_accuracy = (valid["old_label"] == valid[ground_truth_column]).mean()
    new_accuracy = (valid["new_label"] == valid[ground_truth_column]).mean()
    print("\n=== Accuracy voi ground truth ===")
    print(f"Old accuracy: {old_accuracy:.2%}")
    print(f"New accuracy: {new_accuracy:.2%}")
    print("\n=== Confusion matrix moi ===")
    print(pd.crosstab(valid[ground_truth_column], valid["new_label"], dropna=False).to_string())


def main() -> int:
    parser = argparse.ArgumentParser(description="Phan tich collision khong dau va test filename matcher moi.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Duong dan classification_report.csv.")
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS, help="Duong dan data/keywords.json.")
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES, help="Duong dan data/aliases.json.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Thu muc xuat CSV phan tich.")
    parser.add_argument("--ground-truth-column", default=None, help="Cot nhan dung neu ban da bo sung thu cong.")
    args = parser.parse_args()

    df = pd.read_csv(args.report, encoding="utf-8-sig")
    required = {"source", "label", "engine", "top_evidence"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV thieu cot bat buoc: {sorted(missing)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rules = build_rule_set(args.keywords, args.aliases)

    noisy_tokens = analyze_noisy_tokens(df)
    comparison = build_comparison(df, rules)
    filename_comparison = comparison[comparison["old_engine"] == "filename"].copy()
    changed = filename_comparison[filename_comparison["changed"]].copy()

    noisy_tokens.to_csv(args.output_dir / "noisy_tokens.csv", index=False, encoding="utf-8-sig")
    comparison.to_csv(args.output_dir / "filename_matcher_comparison.csv", index=False, encoding="utf-8-sig")
    changed.to_csv(args.output_dir / "changed_labels.csv", index=False, encoding="utf-8-sig")

    print_evaluation(comparison)
    maybe_print_ground_truth_metrics(comparison, args.ground_truth_column)

    print("\n=== Top token gay nhieu trong report cu ===")
    if noisy_tokens.empty:
        print("Khong tim thay token gay nhieu tu top_evidence.")
    else:
        print(noisy_tokens.head(30).to_string(index=False))

    print("\n=== File da xuat ===")
    print(args.output_dir / "noisy_tokens.csv")
    print(args.output_dir / "filename_matcher_comparison.csv")
    print(args.output_dir / "changed_labels.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
