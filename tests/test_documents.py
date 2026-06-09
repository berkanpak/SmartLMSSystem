import pytest
from pathlib import Path
from smart_lms.tools.documents import (
    extract_pdf_text,
    extract_pptx_text,
    extract_document_text,
)

FIXTURES = Path("tests/fixtures")


def test_extract_pdf_text():
    text = extract_pdf_text(str(FIXTURES / "sample.pdf"))
    assert "Power Rule" in text


def test_extract_pptx_text():
    text = extract_pptx_text(str(FIXTURES / "sample.pptx"))
    assert "Chain Rule" in text


def test_extract_document_text_routes_pdf():
    text = extract_document_text(str(FIXTURES / "sample.pdf"))
    assert len(text) > 0


def test_extract_document_text_routes_pptx():
    text = extract_document_text(str(FIXTURES / "sample.pptx"))
    assert len(text) > 0


def test_extract_document_text_unknown_ext_returns_empty():
    text = extract_document_text("file.xyz")
    assert text == ""
