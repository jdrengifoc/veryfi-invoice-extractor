"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from veryfi_invoice_extractor.paths import FIXTURES_DIR


@pytest.fixture
def switch_ocr() -> str:
    """OCR text from a real Switch invoice (cached)."""
    return (FIXTURES_DIR / "switch_ocr_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def non_switch_ocr() -> str:
    """OCR text that does NOT match the Switch template."""
    return (FIXTURES_DIR / "non_switch_ocr.txt").read_text(encoding="utf-8")
