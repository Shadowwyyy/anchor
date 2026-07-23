"""Tests for load_document. PDF reading is injected to avoid a real PDF dependency."""

import pytest

from .loader import (
    DocumentReadError,
    LoadedDocument,
    UnsupportedFileType,
    load_document,
)


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_reads_txt_file(tmp_path):
    path = write(tmp_path, "doc.txt", "Hello world\nsecond line")
    doc = load_document(path)
    assert isinstance(doc, LoadedDocument)
    assert doc.text == "Hello world\nsecond line"
    assert doc.filename == "doc.txt"
    assert doc.source_path == str(path)


def test_reads_md_file(tmp_path):
    path = write(tmp_path, "doc.md", "# Title\n\nBody text")
    doc = load_document(path)
    assert "# Title" in doc.text
    assert "Body text" in doc.text


def test_collapses_excess_blank_lines(tmp_path):
    path = write(tmp_path, "doc.txt", "a\n\n\n\n\nb")
    assert load_document(path).text == "a\n\nb"


def test_collapses_runs_of_spaces(tmp_path):
    path = write(tmp_path, "doc.txt", "word     spaced")
    assert load_document(path).text == "word spaced"


def test_rejoins_hyphenated_linebreaks(tmp_path):
    path = write(tmp_path, "doc.txt", "immi-\ngration law")
    assert "immigration law" in load_document(path).text


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_document(tmp_path / "nope.txt")


def test_unsupported_extension_raises(tmp_path):
    path = write(tmp_path, "doc.docx", "x")
    with pytest.raises(UnsupportedFileType):
        load_document(path)


def test_pdf_uses_injected_reader(tmp_path):
    path = write(tmp_path, "doc.pdf", "ignored")
    doc = load_document(path, pdf_pages=lambda p: ["Page one text", "Page two text"])
    assert "Page one text" in doc.text
    assert "Page two text" in doc.text


def test_pdf_skips_blank_pages(tmp_path):
    path = write(tmp_path, "doc.pdf", "ignored")
    doc = load_document(path, pdf_pages=lambda p: ["Real", "   ", ""])
    assert doc.text == "Real"


def test_pdf_read_failure_raises_document_read_error(tmp_path):
    path = write(tmp_path, "doc.pdf", "ignored")

    def boom(_):
        raise ValueError("encrypted")

    with pytest.raises(DocumentReadError):
        load_document(path, pdf_pages=boom)


def test_loaded_document_is_frozen(tmp_path):
    path = write(tmp_path, "doc.txt", "x")
    doc = load_document(path)
    with pytest.raises(Exception):
        doc.text = "mutated"  # type: ignore[misc]