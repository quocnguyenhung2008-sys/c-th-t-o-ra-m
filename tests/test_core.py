from pathlib import Path

from docsorter.config import ClassificationConfig
from docsorter.classifier import DocumentClassifier, ClassificationStatus
from docsorter.pdf_engine import PdfExtractionResult
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


def test_diacritic_collision_does_not_match_tuong_as_tuong() -> None:
    rules = load_keyword_rules(ROOT / "data" / "keywords.json")
    negative = load_negative_rules(ROOT / "data" / "negative_keywords.json")
    result = score_document(
        filename_text="",
        body_text="Ý tưởng thuật toán dùng hai con trỏ và truy vấn dữ liệu.",
        keyword_rules=rules,
        negative_rules=negative,
        filename_multiplier=2.5,
        body_multiplier=1.0,
    )
    assert "Ngu_van" not in result.scores


def test_accented_tuong_still_matches_ngu_van() -> None:
    rules = load_keyword_rules(ROOT / "data" / "keywords.json")
    negative = load_negative_rules(ROOT / "data" / "negative_keywords.json")
    result = score_document(
        filename_text="",
        body_text="Nghệ thuật tuồng và sân khấu tuồng trong văn học dân gian.",
        keyword_rules=rules,
        negative_rules=negative,
        filename_multiplier=2.5,
        body_multiplier=1.0,
    )
    assert result.scores["Ngu_van"].score >= 40


def test_risky_single_subject_words_do_not_match_body_noise() -> None:
    rules = load_keyword_rules(ROOT / "data" / "keywords.json")
    negative = load_negative_rules(ROOT / "data" / "negative_keywords.json")
    result = score_document(
        filename_text="",
        body_text="Qua trinh hien dai hoa. Van ban phap ly nay su dung phep tinh toan dien tu.",
        keyword_rules=rules,
        negative_rules=negative,
        filename_multiplier=2.5,
        body_multiplier=1.0,
    )
    for subject in ("Hoa_hoc", "Ngu_van", "Lich_su", "Toan"):
        assert subject not in result.scores


def test_administrative_samples_score_as_negative_subjects() -> None:
    rules = load_keyword_rules(ROOT / "data" / "keywords.json")
    negative = load_negative_rules(ROOT / "data" / "negative_keywords.json")
    result = score_document(
        filename_text="2 DS niem yet THPT hoan chinh 2023 2024 Ct",
        body_text="MON TOAN TT SBD ngay sinh hs truong ghi chu MON NGU VAN MON TIENG ANH",
        keyword_rules=rules,
        negative_rules=negative,
        filename_multiplier=2.5,
        body_multiplier=1.0,
    )
    top_subject = max((score.score for score in result.scores.values()), default=0.0)
    assert result.negative_score > top_subject


def test_unknown_pdf_is_retried_with_ocr(monkeypatch, tmp_path: Path) -> None:
    calls = []

    def fake_extract_pdf_text(path, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return PdfExtractionResult(text="", pages_sampled=[0], engine="none", ocr_used=False, errors=[])
        return PdfExtractionResult(text="Bai tap dao ham va nguyen ham", pages_sampled=[0], engine="easyocr", ocr_used=True, errors=[])

    import docsorter.classifier as classifier_module

    monkeypatch.setattr(classifier_module, "extract_pdf_text", fake_extract_pdf_text)
    classifier = DocumentClassifier(ClassificationConfig(ocr_backend="easyocr"))
    result = classifier.classify(tmp_path / "scan.pdf")

    assert len(calls) == 2
    assert calls[1]["enable_ocr"] is True
    assert calls[1]["always_ocr_pdf"] is True
    assert result.status == ClassificationStatus.SUBJECT
    assert result.target_label == "Toan"
    assert result.ocr_used is True
    assert result.extraction_engine == "easyocr:retry_unknown"


def test_prevoi_and_vact_filename_regressions() -> None:
    classifier = DocumentClassifier(ClassificationConfig(excluded_subjects=()))
    cases = {
        "PreVOI 19-11-2025.pdf": "Tin_hoc",
        "Đề VACT dự đoán 1000 - File đề.pdf": "Toan",
    }
    for filename, expected in cases.items():
        result = classifier.classify(Path("/tmp") / filename)
        assert result.status == ClassificationStatus.SUBJECT
        assert result.target_label == expected
        assert result.extraction_engine == "filename"


def test_classifier_marks_unknown_for_empty_supported_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.docx"
    path.write_bytes(
        b"PK\x05\x06" + b"\x00" * 18
    )
    classifier = DocumentClassifier(ClassificationConfig())
    result = classifier.classify(path)
    assert result.status in {ClassificationStatus.ERROR, ClassificationStatus.UNKNOWN}
