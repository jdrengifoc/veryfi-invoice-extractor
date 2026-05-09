# src/veryfi_invoice_extractor/client.py
"""Veryfi API client — handles credentials and API communication."""

import os

from dotenv import load_dotenv
from veryfi import Client


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
