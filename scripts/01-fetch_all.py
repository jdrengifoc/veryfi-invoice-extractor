# scripts/01-fetch_all.py
"""Fetch and cache Veryfi outputs for every PDF in INPUTS_DIR."""

from veryfi_invoice_extractor.client import build_client, fetch_and_cache
from veryfi_invoice_extractor.paths import INPUTS_DIR


def main() -> None:
    """Process every PDF under INPUTS_DIR, caching results to disk."""
    pdf_paths = sorted(INPUTS_DIR.glob("*.pdf"))

    if not pdf_paths:
        print(f"No PDFs found under {INPUTS_DIR}")
        return

    print(f"Found {len(pdf_paths)} PDF(s) under {INPUTS_DIR}")
    client = build_client()

    for i, pdf_path in enumerate(pdf_paths, start=1):
        print(f"[{i}/{len(pdf_paths)}] {pdf_path.name} ... ", end="", flush=True)
        response = fetch_and_cache(pdf_path, client=client, force_refresh=False)
        ocr_len = len(response.get("ocr_text", ""))
        print(f"OK ({ocr_len} chars of ocr_text)")

    print("\nDone. Outputs cached under data/01-veryfi_outputs/")


if __name__ == "__main__":
    main()
