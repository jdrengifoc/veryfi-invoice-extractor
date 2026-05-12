"""Tests for the Switch invoice format validator."""

from __future__ import annotations

from veryfi_invoice_extractor.validator import (
    REQUIRED_ANCHORS,
    is_supported_format,
    missing_anchors,
)


def test_accepts_switch_format(switch_ocr: str) -> None:
    """A real Switch invoice ocr_text must be accepted."""
    assert is_supported_format(switch_ocr) is True


def test_rejects_non_switch_document(non_switch_ocr: str) -> None:
    """Unrelated text must be rejected."""
    assert is_supported_format(non_switch_ocr) is False


def test_rejects_empty_input() -> None:
    """An empty string lacks all anchors and must be rejected."""
    assert is_supported_format("") is False


def test_missing_anchors_lists_all_failures_for_unrelated_text(
    non_switch_ocr: str,
) -> None:
    """For a non-Switch document, every anchor should be reported missing."""
    missing = missing_anchors(non_switch_ocr)
    assert len(missing) == len(REQUIRED_ANCHORS)


def test_missing_anchors_empty_for_valid_input(switch_ocr: str) -> None:
    """A valid Switch ocr_text reports no missing anchors."""
    assert missing_anchors(switch_ocr) == []
