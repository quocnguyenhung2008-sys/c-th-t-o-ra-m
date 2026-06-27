from pathlib import Path

from docsorter.config import ClassificationConfig
from docsorter.classifier import DocumentClassifier, ClassificationStatus
from docsorter.normalize import normalize_text
from docsorter.sampling import sampled_page_indexes
from docsorter.scoring import score_document
from docsorter.keyword_engine import load_keyword_rules, load_negative_rules


ROOT = Path(__file__).resolve().parent.parent


def test_normalize_removes_accents_and_noise() -> None:
    normalized = normalize_text("ĐẠO-HÀM   \n\n Nguyên    hàm")
    assert "dao-ham" in normalized.accentless
    assert "nguyen ham" in normalized.accentless


def test_sampling_uses_first_middle_last_pages() -> None:
    assert sampled_page_indexes(20, 6) == [0, 1, 10, 11, 18, 19]
    assert sampled_page_indexes(3, 6) == [0, 1, 2]


def test_scoring_prioritizes_filename() -> None:
    rules = load_keyword_rules(ROOT / "data" / "keywords.json")
    negative = load_negative_rules(ROOT / "data" / "negative_keywords.json")
    result = score_document(
        filename_text="De cuong dao ham lop 12",
        body_text="Bai tap ham so va tich phan.",
        keyword_rules=rules,
        negative_rules=negative,
        filename_multiplier=2.5,
        body_multiplier=1.0,
    )
    assert result.scores["Toan"].score >= 20


def test_classifier_uses_filename_aliases_for_subject_names() -> None:
    classifier = DocumentClassifier(ClassificationConfig())
    cases = {
        "Tiếng Anh.pdf": "Tieng_Anh",
        "Anh.pdf": "Tieng_Anh",
        "TA.pdf": "Tieng_Anh",
        "Hóa.pdf": "Hoa_hoc",
        "Lý.pdf": "Vat_ly",
        "Văn.pdf": "Ngu_van",
    }
    for filename, expected in cases.items():
        result = classifier.classify(Path("/tmp") / filename)
        assert result.status == ClassificationStatus.SUBJECT
        assert result.target_label == expected
        assert result.extraction_engine == "filename"


def test_short_filename_aliases_do_not_match_inside_names() -> None:
    classifier = DocumentClassifier(ClassificationConfig())
    for filename in ["Phạm Văn Trọng.pdf", "Pham Van Trong.pdf"]:
        result = classifier.classify(Path("/tmp") / filename)
        assert result.target_label != "Ngu_van"


def test_dia_ly_and_gdcd_are_excluded_by_default() -> None:
    classifier = DocumentClassifier(ClassificationConfig())
    for filename in ["Địa.pdf", "GDCD.pdf"]:
        result = classifier.classify(Path("/tmp") / filename)
        assert result.target_label not in {"Dia_ly", "GDCD"}


def test_classifier_marks_unknown_for_empty_supported_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.docx"
    path.write_bytes(
        b"PK\x05\x06" + b"\x00" * 18
    )
    classifier = DocumentClassifier(ClassificationConfig())
    result = classifier.classify(path)
    assert result.status in {ClassificationStatus.ERROR, ClassificationStatus.UNKNOWN}
