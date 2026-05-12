"""Tests for the Switch invoice parser."""

from __future__ import annotations

from veryfi_invoice_extractor.parser import extract_by_anchor, parse_invoice, to_float


class TestToFloat:
    """Tests for the to_float numeric parser."""

    def test_parses_positive(self) -> None:
        assert to_float("1,234,567.89") == 1234567.89

    def test_parses_positive_with_plus(self) -> None:
        assert to_float("+1,234,567.89") == 1234567.89

    def test_parses_zero(self) -> None:
        assert to_float("0.00") == 0.00

    def test_parses_negative(self) -> None:
        assert to_float("-1,234.56") == -1234.56


class TestExtractByAnchor:
    """Tests for the anchor-based row extractor."""

    def test_returns_n_th_row_after_anchor(self) -> None:
        text = "Header\nAnchor row\n1\n2\n3"
        assert extract_by_anchor(text, "Anchor", relative_row=1) == "1"
        assert extract_by_anchor(text, "Anchor", relative_row=3) == "3"

    def test_returns_none_when_invalid_anchor(self) -> None:
        assert extract_by_anchor("no anchor here", "invalid anchor", 1) is None

    def test_returns_none_when_invalid_relative_row(self) -> None:
        text = "Header\nAnchor row\n1\n2\n3"
        assert extract_by_anchor(text, "Anchor", 4) is None

    def test_skips_empty_lines(self) -> None:
        text = "Header\nAnchor row\n1\n\n2\n\n\n3"
        assert extract_by_anchor(text, "Anchor", relative_row=2) == "2"
        assert extract_by_anchor(text, "Anchor", relative_row=3) == "3"


class TestParseInvoice:
    """End-to-end tests against a real Switch ocr_text."""

    def test_returns_expected_top_level_fields(self, switch_ocr: str) -> None:
        invoice = parse_invoice(switch_ocr)
        expected = {
            "vendor_name",
            "vendor_address",
            "bill_to_name",
            "invoice_number",
            "date",
            "total",
            "line_items",
        }
        assert set(invoice.keys()) == expected

    def test_extracts_vendor_name(self, switch_ocr: str) -> None:
        invoice = parse_invoice(switch_ocr)
        assert invoice["vendor_name"] is not None
        assert "Switch" in invoice["vendor_name"]

    def test_extracts_total_as_float(self, switch_ocr: str) -> None:
        invoice = parse_invoice(switch_ocr)
        assert isinstance(invoice["total"], float)
        assert invoice["total"] != 0

    def test_extracts_at_least_one_line_item(self, switch_ocr: str) -> None:
        invoice = parse_invoice(switch_ocr)
        assert len(invoice["line_items"]) >= 1

    def test_line_items_have_required_fields(self, switch_ocr: str) -> None:
        invoice = parse_invoice(switch_ocr)
        expected_keys = {"sku", "description", "quantity", "tax_rate", "price", "total"}
        for item in invoice["line_items"]:
            assert set(item.keys()) == expected_keys

    def test_parse_invoice_handles_empty_text(self) -> None:
        """Defensive: empty input must not crash; all fields should be None or empty."""
        invoice = parse_invoice("")
        assert invoice["vendor_name"] is None
        assert invoice["total"] is None
        assert invoice["line_items"] == []
