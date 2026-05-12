# scripts/03-check_determinism.py
"""Check whether Veryfi OCR output changes across repeated calls."""

from veryfi_invoice_extractor.client import build_client
from veryfi_invoice_extractor.paths import INPUTS_DIR


PDF_NAME = "synth-switch_v5-14.pdf"
RUNS = 3


def main() -> None:
    pdf_path = INPUTS_DIR / PDF_NAME

    client = build_client()

    outputs: list[str] = []

    print(f"Running {RUNS} calls for {PDF_NAME}\n")

    for i in range(RUNS):
        response = client.process_document(
            file_path=str(pdf_path),
            delete_after_processing=True,
        )

        ocr_text = response.get("ocr_text", "")
        outputs.append(ocr_text)

        print(f"Run {i + 1}: {len(ocr_text)} chars")

    deterministic = len(set(outputs)) == 1

    print(f"\nDeterministic: {deterministic}")


if __name__ == "__main__":
    main()
