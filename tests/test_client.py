"""Tests for the Veryfi client wrapper."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from veryfi_invoice_extractor.client import _load_secret, fetch_and_cache


class TestLoadSecret:
    """Tests for the _load_secret helper."""

    def test_returns_value_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns the env var value when it is set."""
        monkeypatch.setenv("MY_SECRET", "abc123")
        assert _load_secret("MY_SECRET") == "abc123"

    def test_raises_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raises a clear RuntimeError when the env var is unset."""
        monkeypatch.delenv("MY_SECRET", raising=False)
        with pytest.raises(RuntimeError, match="Missing required environment variable"):
            _load_secret("MY_SECRET")

    def test_treats_empty_string_as_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty string is treated as missing — fail-fast preferable."""
        monkeypatch.setenv("MY_SECRET", "")
        with pytest.raises(RuntimeError, match="Missing required environment variable"):
            _load_secret("MY_SECRET")


class TestFetchAndCache:
    """Tests for the cache-aware fetch_and_cache function."""

    def test_returns_cached_response_without_api_call(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When both cache files exist, the API client is never called."""
        monkeypatch.setattr(
            "veryfi_invoice_extractor.client.VERYFI_OUTPUTS_DIR", tmp_path
        )
        # Simulates raw files.
        pdf_path = tmp_path / "fake.pdf"
        pdf_path.touch()

        # Simulates fetch outputs.
        cached = {"ocr_text": "cached content", "vendor": "Switch"}
        (tmp_path / "fake_full.json").write_text(json.dumps(cached))
        (tmp_path / "fake_ocr.txt").write_text("cached content")

        mock_client = MagicMock()
        result = fetch_and_cache(pdf_path, client=mock_client)

        # The content was extracted correcty?
        assert result == cached

        # Cached memory was employ instead of using the client.
        mock_client.process_document.assert_not_called()

    def test_calls_api_when_cache_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When cache is empty, the API is called and results are persisted."""
        monkeypatch.setattr(
            "veryfi_invoice_extractor.client.VERYFI_OUTPUTS_DIR", tmp_path
        )
        # Simulated raw files.
        pdf_path = tmp_path / "fake.pdf"
        pdf_path.touch()

        # Simulates the api response without consuming resources.
        api_response = {"ocr_text": "fresh from API", "vendor": "Switch"}
        mock_client = MagicMock()
        mock_client.process_document.return_value = api_response
        result = fetch_and_cache(pdf_path, client=mock_client)

        # Test if the api was "called" and correctly returns the "response".
        assert result == api_response
        mock_client.process_document.assert_called_once()

        # Wrote correctly the files.
        assert (tmp_path / "fake_full.json").exists()
        assert (tmp_path / "fake_ocr.txt").exists()
        assert (tmp_path / "fake_ocr.txt").read_text() == "fresh from API"

    def test_force_refresh_bypasses_cache(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """force_refresh=True calls the API even when cache exists."""
        monkeypatch.setattr(
            "veryfi_invoice_extractor.client.VERYFI_OUTPUTS_DIR", tmp_path
        )

        # Simulated raw files.
        pdf_path = tmp_path / "fake.pdf"
        pdf_path.touch()

        # Simulates fetch outputs.
        (tmp_path / "fake_full.json").write_text(json.dumps({"old": "cache"}))
        (tmp_path / "fake_ocr.txt").write_text("old")

        # Simulates the api response without consuming resources.
        api_response = {"ocr_text": "fresh from API", "vendor": "Switch"}
        mock_client = MagicMock()
        mock_client.process_document.return_value = api_response
        result = fetch_and_cache(pdf_path, client=mock_client, force_refresh=True)

        # Test if the api was "called" and correctly returns the "response".
        assert result == api_response
        mock_client.process_document.assert_called_once()
