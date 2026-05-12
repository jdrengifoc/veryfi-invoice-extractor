# scripts/02-process.py
"""Process every cached ocr_text: validate, parse, and persist as JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from veryfi_invoice_extractor.paths import LOGS_DIR, RESULTS_DIR, VERYFI_OUTPUTS_DIR
from veryfi_invoice_extractor.validator import is_supported_format, missing_anchors
from veryfi_invoice_extractor.parser import parse_invoice

LOG_FILE = LOGS_DIR / "process.log"
logger = logging.getLogger(__name__)


def save_invoice(invoice: dict, txt_path: Path) -> Path:
    """Persist the parsed invoice as JSON in RESULTS_DIR."""
    base_name = txt_path.stem.removesuffix("_ocr")
    output_path = RESULTS_DIR / f"{base_name}.json"
    output_path.write_text(
        json.dumps(invoice, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, mode="a"),
        ],
    )

    txt_paths = sorted(VERYFI_OUTPUTS_DIR.glob("*.txt"))
    processed = 0
    rejected = 0

    for txt_path in txt_paths:
        text = txt_path.read_text(encoding="utf-8")

        if not is_supported_format(text):
            logger.warning(
                "REJECTED %s — missing anchors: %s",
                txt_path.name,
                missing_anchors(text),
            )
            rejected += 1
            continue

        invoice = parse_invoice(text)
        output_path = save_invoice(invoice, txt_path)
        logger.info("PROCESSED %s → %s", txt_path.name, output_path.name)
        processed += 1

    logger.info("Done. Processed: %d | Rejected: %d", processed, rejected)


if __name__ == "__main__":
    main()
