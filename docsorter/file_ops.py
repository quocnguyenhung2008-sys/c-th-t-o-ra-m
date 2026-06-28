from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .classifier import DocumentClassification
from .config import ClassificationConfig


@dataclass(frozen=True)
class MoveResult:
    source: Path
    destination: Path
    action: str


def discover_files(root: Path, config: ClassificationConfig, exclude_roots: tuple[Path, ...] = ()) -> list[Path]:
    patterns: list[str] = []
    if config.include_docx:
        patterns.append("*.docx")
    if config.include_pdf:
        patterns.append("*.pdf")
    iterator = root.rglob if config.recursive else root.glob
    files: list[Path] = []
    resolved_excludes = tuple(path.resolve() for path in exclude_roots)
    for pattern in patterns:
        files.extend(
            path
            for path in iterator(pattern)
            if path.is_file()
            and not path.name.startswith("~$")
            and not _is_inside_any(path, resolved_excludes)
        )
    return sorted(set(files))


def _is_inside_any(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved_path = path.resolve()
    return any(resolved_path == root or root in resolved_path.parents for root in roots)


def place_file(
    classification: DocumentClassification,
    output_root: Path,
    config: ClassificationConfig,
) -> MoveResult:
    destination_dir = output_root / classification.target_label
    destination = _unique_destination(destination_dir / classification.path.name, config.overwrite)
    if config.dry_run:
        return MoveResult(classification.path, destination, "dry-run")
    destination_dir.mkdir(parents=True, exist_ok=True)
    if config.copy:
        shutil.copy2(classification.path, destination)
        return MoveResult(classification.path, destination, "copied")
    shutil.move(str(classification.path), str(destination))
    return MoveResult(classification.path, destination, "moved")


def _unique_destination(destination: Path, overwrite: bool) -> Path:
    if overwrite or not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 2
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
