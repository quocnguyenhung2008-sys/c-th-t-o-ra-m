from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .config import ClassificationConfig
from .docx_engine import extract_docx_text
from .keyword_engine import load_alias_rules, load_keyword_rules, load_negative_rules
from .pdf_engine import PdfExtractionResult, extract_pdf_text
from .scoring import MatchEvidence, ScoreResult, score_document


class ClassificationStatus(str, Enum):
    SUBJECT = "subject"
    UNKNOWN = "unknown"
    NON_SUBJECT = "non_subject"
    CONFLICT = "conflict"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


@dataclass(frozen=True)
class DocumentClassification:
    path: Path
    status: ClassificationStatus
    target_label: str
    score: float
    runner_up_score: float
    negative_score: float
    evidence: list[MatchEvidence]
    pages_sampled: list[int]
    extraction_engine: str
    ocr_used: bool
    error: str = ""


class DocumentClassifier:
    def __init__(self, config: ClassificationConfig) -> None:
        self.config = config
        excluded_subjects = set(config.excluded_subjects)
        self.keyword_rules = [
            rule for rule in load_keyword_rules(config.keywords_path) if rule.subject not in excluded_subjects
        ]
        self.negative_rules = load_negative_rules(config.negative_keywords_path)
        self.alias_rules = [
            rule
            for rule in load_alias_rules(config.aliases_path, config.filename_alias_weight)
            if rule.subject not in excluded_subjects
        ]

    def classify(self, path: Path) -> DocumentClassification:
        filename_score = score_document(
            filename_text=path.stem,
            body_text="",
            keyword_rules=self.keyword_rules,
            negative_rules=self.negative_rules,
            filename_multiplier=self.config.filename_weight_multiplier,
            body_multiplier=self.config.body_weight_multiplier,
            filename_alias_rules=self.alias_rules,
        )
        filename_status, filename_label, filename_top, filename_runner_up, filename_evidence = self._decide(
            filename_score
        )
        if (
            filename_status == ClassificationStatus.SUBJECT
            and filename_top >= self.config.filename_fast_path_score
        ):
            return DocumentClassification(
                path=path,
                status=filename_status,
                target_label=filename_label,
                score=filename_top,
                runner_up_score=filename_runner_up,
                negative_score=filename_score.negative_score,
                evidence=filename_evidence,
                pages_sampled=[],
                extraction_engine="filename",
                ocr_used=False,
            )

        try:
            body_text, pdf_result = self._extract_text(path)
        except Exception as exc:
            return DocumentClassification(
                path=path,
                status=ClassificationStatus.ERROR,
                target_label=self.config.unknown_dir_name,
                score=0.0,
                runner_up_score=0.0,
                negative_score=0.0,
                evidence=[],
                pages_sampled=[],
                extraction_engine="error",
                ocr_used=False,
                error=str(exc),
            )

        if body_text is None:
            return DocumentClassification(
                path=path,
                status=ClassificationStatus.UNSUPPORTED,
                target_label=self.config.unknown_dir_name,
                score=0.0,
                runner_up_score=0.0,
                negative_score=0.0,
                evidence=[],
                pages_sampled=[],
                extraction_engine="unsupported",
                ocr_used=False,
            )

        score_result = score_document(
            filename_text=path.stem,
            body_text=body_text,
            keyword_rules=self.keyword_rules,
            negative_rules=self.negative_rules,
            filename_multiplier=self.config.filename_weight_multiplier,
            body_multiplier=self.config.body_weight_multiplier,
            filename_alias_rules=self.alias_rules,
        )
        status, label, top_score, runner_up, evidence = self._decide(score_result)
        if self._should_retry_unknown_pdf_with_ocr(path, status, pdf_result):
            retry = self._classify_pdf_with_ocr_retry(path)
            if retry is not None:
                return retry
        return DocumentClassification(
            path=path,
            status=status,
            target_label=label,
            score=top_score,
            runner_up_score=runner_up,
            negative_score=score_result.negative_score,
            evidence=evidence,
            pages_sampled=pdf_result.pages_sampled if pdf_result else [],
            extraction_engine=pdf_result.engine if pdf_result else "docx",
            ocr_used=pdf_result.ocr_used if pdf_result else False,
            error="; ".join(pdf_result.errors) if pdf_result and pdf_result.errors else "",
        )

    def _should_retry_unknown_pdf_with_ocr(
        self,
        path: Path,
        status: ClassificationStatus,
        pdf_result: PdfExtractionResult | None,
    ) -> bool:
        return (
            self.config.retry_unknown_with_ocr
            and path.suffix.lower() == ".pdf"
            and status == ClassificationStatus.UNKNOWN
            and pdf_result is not None
            and not pdf_result.ocr_used
            and self.config.ocr_backend != "none"
        )

    def _classify_pdf_with_ocr_retry(self, path: Path) -> DocumentClassification | None:
        pdf_result = extract_pdf_text(
            path,
            max_pages=self.config.max_pdf_pages,
            min_chars_before_ocr=self.config.min_extracted_chars_before_ocr,
            enable_ocr=True,
            always_ocr_pdf=True,
            ocr_backend=self.config.ocr_backend,
        )
        score_result = score_document(
            filename_text=path.stem,
            body_text=pdf_result.text,
            keyword_rules=self.keyword_rules,
            negative_rules=self.negative_rules,
            filename_multiplier=self.config.filename_weight_multiplier,
            body_multiplier=self.config.body_weight_multiplier,
            filename_alias_rules=self.alias_rules,
        )
        status, label, top_score, runner_up, evidence = self._decide(score_result)
        if status == ClassificationStatus.UNKNOWN:
            return None
        return DocumentClassification(
            path=path,
            status=status,
            target_label=label,
            score=top_score,
            runner_up_score=runner_up,
            negative_score=score_result.negative_score,
            evidence=evidence,
            pages_sampled=pdf_result.pages_sampled,
            extraction_engine=f"{pdf_result.engine}:retry_unknown",
            ocr_used=pdf_result.ocr_used,
            error="; ".join(pdf_result.errors) if pdf_result.errors else "",
        )

    def _extract_text(self, path: Path) -> tuple[str | None, PdfExtractionResult | None]:
        suffix = path.suffix.lower()
        if suffix == ".docx" and self.config.include_docx:
            return extract_docx_text(path), None
        if suffix == ".pdf" and self.config.include_pdf:
            result = extract_pdf_text(
                path,
                max_pages=self.config.max_pdf_pages,
                min_chars_before_ocr=self.config.min_extracted_chars_before_ocr,
                enable_ocr=self.config.enable_ocr,
                always_ocr_pdf=self.config.always_ocr_pdf,
                ocr_backend=self.config.ocr_backend,
            )
            return result.text, result
        if self.config.include_other:
            return "", None
        return None, None

    def _decide(
        self, score_result: ScoreResult
    ) -> tuple[ClassificationStatus, str, float, float, list[MatchEvidence]]:
        ranked = sorted(score_result.scores.values(), key=lambda item: item.score, reverse=True)
        if not ranked:
            if score_result.negative_score >= self.config.min_score:
                return (
                    ClassificationStatus.NON_SUBJECT,
                    self.config.non_subject_dir_name,
                    0.0,
                    0.0,
                    score_result.negative_evidence,
                )
            return ClassificationStatus.UNKNOWN, self.config.unknown_dir_name, 0.0, 0.0, []

        top = ranked[0]
        runner_up_score = ranked[1].score if len(ranked) > 1 else 0.0
        margin = top.score - runner_up_score

        # ── ĐỀ THI: Xử lý logic đặc biệt ────────────────────────────────
        # Nguyên tắc: "Đề thi" phải đủ ngưỡng CAO hơn để xác nhận.
        # Ngăn tài liệu học bình thường bị nhầm vào thư mục Đề thi.
        if top.subject == "De_thi":
            if top.score < self.config.de_thi_min_score:
                # Điểm De_thi không đủ ngưỡng riêng → xét môn học tiếp theo
                if len(ranked) > 1:
                    second = ranked[1]
                    second_runner_up = ranked[2].score if len(ranked) > 2 else 0.0
                    second_margin = second.score - second_runner_up
                    if second.score >= self.config.min_score:
                        if second_runner_up > 0 and second_margin < self.config.min_margin:
                            return ClassificationStatus.CONFLICT, self.config.conflict_dir_name, second.score, second_runner_up, second.evidence
                        return ClassificationStatus.SUBJECT, second.subject, second.score, second_runner_up, second.evidence
                return ClassificationStatus.UNKNOWN, self.config.unknown_dir_name, top.score, runner_up_score, top.evidence
            # Điểm đủ → phân loại là Đề thi, bất kể môn học nào cũng nhường
            return ClassificationStatus.SUBJECT, "De_thi", top.score, runner_up_score, top.evidence

        # Nếu De_thi là runner-up với điểm đủ ngưỡng nhưng top là môn học → ưu tiên môn học
        # (tránh nhầm bài luyện tập có từ "đề thi" vào De_thi)

        if score_result.negative_score > top.score and score_result.negative_score >= self.config.min_score:
            return (
                ClassificationStatus.NON_SUBJECT,
                self.config.non_subject_dir_name,
                top.score,
                runner_up_score,
                score_result.negative_evidence,
            )
        if top.score < self.config.min_score:
            return ClassificationStatus.UNKNOWN, self.config.unknown_dir_name, top.score, runner_up_score, top.evidence
        if runner_up_score > 0 and margin < self.config.min_margin:
            # Kiểm tra xem runner_up có phải De_thi không → nếu có thì bỏ qua conflict
            if len(ranked) > 1 and ranked[1].subject == "De_thi":
                return ClassificationStatus.SUBJECT, top.subject, top.score, runner_up_score, top.evidence
            return ClassificationStatus.CONFLICT, self.config.conflict_dir_name, top.score, runner_up_score, top.evidence
        return ClassificationStatus.SUBJECT, top.subject, top.score, runner_up_score, top.evidence
