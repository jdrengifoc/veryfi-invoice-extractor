# Veryfi Invoice Extractor
Extract structured invoice data from `ocr_text` returned by the Veryfi API. Submitted as the technical test for the Data Annotations Engineer role.

## Development

### Initial setup

Clone the repository and sync dependencies. `uv sync` reads `pyproject.toml`
and `uv.lock` to create a `.venv/` with the exact versions used during
development.

```bash
git clone https://github.com/jdrengifoc13/veryfi-invoice-extractor.git
cd veryfi-invoice-extractor
uv sync
```

Then create your local `.env` from the template and fill in your Veryfi
credentials:

```bash
cp .env.example .env
# edit .env with your VERYFI_CLIENT_ID, VERYFI_CLIENT_SECRET, VERYFI_USERNAME, VERYFI_API_KEY
```

### Quality checks

The project uses four tools for code quality. All four should pass before
committing.

```bash
uv run ruff format .       # auto-format the codebase
uv run ruff check .        # lint: imports, unused code, naming, docstrings, etc.
uv run mypy                # static type-check src/ in strict mode
uv run pytest              # run unit tests with coverage
```

Configuration for each tool lives in `pyproject.toml`.

### Running the sandbox

The sandbox script processes one invoice via the Veryfi API and persists
the raw response and isolated `ocr_text` for inspection:

```bash
uv run python scripts/sandbox.py
```

Outputs are written to `data/01-veryfi_outputs/`. Make sure your Veryfi
credentials are set in `.env` before running.

## AI assistance disclosure

This project was developed with assistance from a large language model
(Claude by Anthropic) for design discussion, code review, and
documentation drafting. All architectural and parsing decisions were
authored and reviewed by me.

---

*Juan David Rengifo Castro · May 2026*