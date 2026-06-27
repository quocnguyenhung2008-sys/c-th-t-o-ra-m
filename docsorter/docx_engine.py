from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree


WORD_NAMESPACES = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class DocxExtractionError(RuntimeError):
    pass


def extract_docx_text(path: Path) -> str:
    try:
        import docx  # type: ignore

        document = docx.Document(str(path))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    parts.append(cell.text)
        return "\n".join(part for part in parts if part)
    except ImportError:
        return _extract_docx_text_stdlib(path)
    except Exception as exc:
        raise DocxExtractionError(f"Cannot extract DOCX text from {path}: {exc}") from exc


def _extract_docx_text_stdlib(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
    except Exception as exc:
        raise DocxExtractionError(f"Cannot read DOCX package {path}: {exc}") from exc

    root = ElementTree.fromstring(xml)
    text_nodes = root.findall(".//w:t", WORD_NAMESPACES)
    return "\n".join(node.text or "" for node in text_nodes)
