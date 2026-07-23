"""Load source documents from disk into cleaned text with metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

TEXT_EXTENSIONS = {".txt", ".md"}
PDF_EXTENSION = ".pdf"


@dataclass(frozen=True)
class LoadedDocument:
    text: str
    source_path: str
    filename: str


class UnsupportedFileType(Exception):
    pass


class DocumentReadError(Exception):
    pass


def _clean(text: str) -> str:
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _read_pdf(path: Path, extract_pages: Callable[[Path], list[str]]) -> str:
    try:
        pages = extract_pages(path)
    except Exception as exc:
        raise DocumentReadError(f"Could not read PDF: {path}") from exc
    return "\n\n".join(page for page in pages if page.strip())


def _default_pdf_pages(path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def load_document(
    path: str | Path,
    pdf_pages: Callable[[Path], list[str]] = _default_pdf_pages,
) -> LoadedDocument:
    """Read a .pdf, .txt, or .md file into cleaned text with source metadata.

    Raises FileNotFoundError if the path is missing, UnsupportedFileType for
    other extensions, and DocumentReadError if the file cannot be parsed.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {path}")

    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            raise DocumentReadError(f"Could not read text file: {path}") from exc
    elif suffix == PDF_EXTENSION:
        raw = _read_pdf(path, pdf_pages)
    else:
        raise UnsupportedFileType(f"Unsupported file type: {suffix or '(none)'}")

    return LoadedDocument(
        text=_clean(raw),
        source_path=str(path),
        filename=path.name,
    )