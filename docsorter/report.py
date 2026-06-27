from __future__ import annotations

import csv
from pathlib import Path

from .classifier import DocumentClassification
from .file_ops import MoveResult


def write_report(path: Path, rows: list[tuple[DocumentClassification, MoveResult]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "source",
                "destination",
                "action",
                "status",
                "label",
                "score",
                "runner_up_score",
                "negative_score",
                "engine",
                "ocr_used",
                "pages_sampled_1_based",
                "top_evidence",
                "notes",
            ]
        )
        for classification, move_result in rows:
            evidence = "; ".join(
                f"{item.source}:{item.keyword} x{item.count}={item.score:.1f}"
                for item in classification.evidence[:10]
            )
            pages = ",".join(str(page + 1) for page in classification.pages_sampled)
            writer.writerow(
                [
                    str(move_result.source),
                    str(move_result.destination),
                    move_result.action,
                    classification.status.value,
                    classification.target_label,
                    f"{classification.score:.2f}",
                    f"{classification.runner_up_score:.2f}",
                    f"{classification.negative_score:.2f}",
                    classification.extraction_engine,
                    str(classification.ocr_used),
                    pages,
                    evidence,
                    classification.error,
                ]
            )
