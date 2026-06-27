from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class ClassificationConfig:
    keywords_path: Path = DATA_DIR / "keywords.json"
    negative_keywords_path: Path = DATA_DIR / "negative_keywords.json"
    aliases_path: Path = DATA_DIR / "aliases.json"
    unknown_dir_name: str = "_Khong_xac_dinh"
    non_subject_dir_name: str = "_Khong_phai_mon_hoc"
    conflict_dir_name: str = "_Can_kiem_tra"
    min_score: float = 8.0
    min_margin: float = 3.0
    filename_weight_multiplier: float = 2.5
    body_weight_multiplier: float = 1.0
    filename_alias_weight: float = 12.0
    filename_fast_path_score: float = 22.0
    excluded_subjects: tuple[str, ...] = ("Dia_ly", "GDCD")
    max_pdf_pages: int = 6
    min_extracted_chars_before_ocr: int = 250
    enable_ocr: bool = False
    always_ocr_pdf: bool = False
    ocr_backend: str = "none"
    dry_run: bool = False
    copy: bool = False
    overwrite: bool = False
    recursive: bool = False
    include_pdf: bool = True
    include_docx: bool = True
    include_other: bool = False
    report_name: str = "classification_report.csv"
