# src/veryfi_invoice_extractor/client.py
"""Veryfi API client — handles credentials and API communication."""

import os
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from veryfi import Client

from veryfi_invoice_extractor.paths import VERYFI_OUTPUTS_DIR


def _load_secret(key: str) -> str:
    """Read a required environment variable; raise if missing."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}. ")

    return value


def build_client() -> Client:
    """Build a Veryfi client using credentials from environment variables."""
    load_dotenv()
    client = Client(
        client_id=_load_secret("VERYFI_CLIENT_ID"),
        client_secret=_load_secret("VERYFI_CLIENT_SECRET"),
        username=_load_secret("VERYFI_USERNAME"),
        api_key=_load_secret("VERYFI_API_KEY"),
    )

    return client


def fetch_and_cache(
    pdf_path: Path,
    *,  # keyword-only.
    client: Client | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Process a PDF via Veryfi and cache outputs locally.

    Two files are persisted under ``VERYFI_OUTPUTS_DIR``:

    - ``<stem>_full.json``: the complete API response (for inspection).
    - ``<stem>_ocr.txt``: the isolated ``ocr_text`` (the parser's input).

    If both cache files already exist and ``force_refresh`` is False, the
    full response is returned from disk without calling the API. This
    protects the trial quota during iterative development.

    Args:
        pdf_path: Path to the source PDF.
        client: Optional pre-built Veryfi client; built on demand if None.
        force_refresh: When True, ignore cache and re-call the API.

    Returns:
        The full Veryfi response as a dictionary.
    """
    VERYFI_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    full_path = VERYFI_OUTPUTS_DIR / f"{pdf_path.stem}_full.json"
    ocr_path = VERYFI_OUTPUTS_DIR / f"{pdf_path.stem}_ocr.txt"

    if not force_refresh and full_path.exists() and ocr_path.exists():
        data = json.loads(full_path.read_text())
        return data if isinstance(data, dict) else {}

    if client is None:
        client = build_client()

    response: dict[str, Any] = client.process_document(
        file_path=str(pdf_path),
        delete_after_processing=True,
    )

    full_path.write_text(json.dumps(response, indent=2, ensure_ascii=False))
    ocr_path.write_text(response.get("ocr_text", ""))

    return response
