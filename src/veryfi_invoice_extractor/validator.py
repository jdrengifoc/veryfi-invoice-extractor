"""Validate that an ocr_text matches the Switch invoice template."""

from __future__ import annotations

import re

# Structural fingerprints of the Switch invoice template.
# A document must contain ALL of these to be considered supported.
REQUIRED_ANCHORS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Invoice Date\s+Due Date\s+Invoice No\."),
    re.compile(r"Description\s+Quantity\s+Rate\s+Amount"),
    re.compile(r"Total\s+USD"),
    re.compile(r"Please make payments to:\s*Switch"),
)


def is_supported_format(ocr_text: str) -> bool:
    """Return True if the ocr_text matches the Switch invoice template."""
    return all(pattern.search(ocr_text) for pattern in REQUIRED_ANCHORS)


def missing_anchors(ocr_text: str) -> list[str]:
    """Return the anchor patterns that did NOT match — useful for debugging."""
    return [
        pattern.pattern for pattern in REQUIRED_ANCHORS if not pattern.search(ocr_text)
    ]
