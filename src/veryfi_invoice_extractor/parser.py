"""Parse Switch invoice ocr_text into structured data."""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Regex building blocks
# ---------------------------------------------------------------------------

NUMBER = r"-?[\d,]+\.\d{2}"

LINE_ITEM_REGEX = re.compile(
    rf"^(?P<description>.+?)\s+"
    rf"(?P<quantity>{NUMBER})\s+"
    rf"(?P<price>{NUMBER})\s+"
    rf"(?P<total>{NUMBER})\s*$",
    re.MULTILINE,
)

VENDOR_NAME_REGEX = re.compile(r"Please make payments to:\s*(.*)")
PO_BOX_REGEX = re.compile(r"PO Box\s+\d+", re.IGNORECASE)
GEO_REGEX = re.compile(
    r"([A-Z][a-z]+(?: [A-Z][a-z]+)*),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)"
)
INVOICE_HEADER_REGEX = re.compile(
    r"(?P<invoice_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<due_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<invoice_no>\d+)"
)
TOTAL_REGEX = re.compile(rf"Total USD\s*\$\s*({NUMBER})")

# Fields not exposed by the Switch invoice template at the line-item level.
# Documented in APPROACH.md.
OMITTED_LINE_FIELDS: dict[str, None] = {
    "sku": None,
    "tax_rate": None,
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def to_float(num_str: str) -> float:
    """Convert a number string like '2,720,985.49' or '-561.00' to float."""
    return float(num_str.replace(",", ""))


def extract_by_anchor(text: str, anchor: str, relative_row: int) -> str | None:
    """Return the n-th non-empty row after the first line containing `anchor`."""
    rows = text.splitlines()
    for i, row in enumerate(rows):
        if anchor in row:
            non_empty = [r for r in rows[i + 1 :] if r.strip()]
            if len(non_empty) >= relative_row:
                return non_empty[relative_row - 1].strip()
    return None


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------


def extract_vendor_name(text: str) -> str | None:
    """Extract the vendor name from the 'Please make payments to:' line."""
    match = VENDOR_NAME_REGEX.search(text)
    return match.group(1).strip() if match else None


def extract_vendor_address(text: str) -> str | None:
    """Concatenate PO Box and 'City, ST ZIP' if both are present."""
    po_box = PO_BOX_REGEX.search(text)
    geo = GEO_REGEX.search(text)

    parts: list[str] = []
    if po_box:
        parts.append(po_box.group(0))
    if geo:
        parts.append(f"{geo.group(1)}, {geo.group(2)} {geo.group(3)}")

    return ", ".join(parts) if parts else None


def extract_bill_to_name(text: str) -> str | None:
    """Locate the bill-to name relative to the 'Invoice No.' anchor."""
    return extract_by_anchor(text, "Invoice No.", relative_row=2)


def extract_invoice_number(text: str) -> str | None:
    """Extract the invoice number from the header row."""
    match = INVOICE_HEADER_REGEX.search(text)
    return match.group("invoice_no") if match else None


def extract_date(text: str) -> str | None:
    """Extract the invoice date from the header row."""
    match = INVOICE_HEADER_REGEX.search(text)
    return match.group("invoice_date") if match else None


def extract_total(text: str) -> float | None:
    """Extract the invoice grand total as a float."""
    match = TOTAL_REGEX.search(text)
    return to_float(match.group(1)) if match else None


def extract_line_items(text: str) -> list[dict[str, object]]:
    """Extract every line item from the table block.

    Each item exposes description, quantity, price, total. The fields
    `sku` and `tax_rate` are set to None because the Switch template
    does not expose them at the line-item level.
    """
    start = re.search(r"Description\s+Quantity\s+Rate\s+Amount", text)
    end = re.search(r"Total\s+USD", text)
    if not start or not end:
        return []

    items_block = text[start.end() : end.start()]
    lines = items_block.splitlines()

    items: list[dict[str, object]] = []
    i = 0
    while i < len(lines):
        match = LINE_ITEM_REGEX.match(lines[i])
        if not match:
            i += 1
            continue

        description = match.group("description").strip()

        # Continuation: non-matching lines belong to the same description.
        j = i + 1
        while j < len(lines) and not LINE_ITEM_REGEX.match(lines[j]):
            if lines[j].strip():
                description += " " + lines[j].strip()
            j += 1

        items.append(
            {
                **OMITTED_LINE_FIELDS,
                "description": description,
                "quantity": to_float(match.group("quantity")),
                "price": to_float(match.group("price")),
                "total": to_float(match.group("total")),
            }
        )
        i = j

    return items


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def parse_invoice(text: str) -> dict[str, object]:
    """Run every field extractor against the given ocr_text."""
    return {
        "vendor_name": extract_vendor_name(text),
        "vendor_address": extract_vendor_address(text),
        "bill_to_name": extract_bill_to_name(text),
        "invoice_number": extract_invoice_number(text),
        "date": extract_date(text),
        "total": extract_total(text),
        "line_items": extract_line_items(text),
    }
