# Methodology

## 1. Problem statement

Veryfi's API provides a fully structured representation of an invoice (vendor, totals, line items, etc.), but the test instructs us to ignore everything in the response except the raw transcribed text of the document (the `ocr_text` field) and rebuild the structured representation from that text.

The deliverable extracts six top-level fields (`vendor_name`, `vendor_address`, `bill_to_name`, `invoice_number`, `date`, and a list of `line_items`), where each line item has six sub-fields (`sku`, `description`, `quantity`, `tax_rate`, `price`, `total`). The system must accept documents that match the Switch invoice template and explicitly reject any other document.

## 2. System overview

The pipeline is three stages, each in its own module:

```
PDF  →  Veryfi API  →  ocr_text  →  validator  →  parser  →  JSON
       (client.py)                (validator.py) (parser.py)
```

- **`client.py`**: builds the Veryfi client from `.env` credentials and the function `fetch_and_cache(pdf_path)` calls the API only when no cached output exists for the PDF.
- **`validator.py`**: decides whether an `ocr_text` matches the Switch template by checking a tuple of structural anchors.
- **`parser.py`**: extracts every requested field via regex.

Two scripts orchestrate the stages:

- `scripts/01-fetch_all.py` iterates over PDFs in `data/00-inputs/` and
  caches the API responses to `data/01-veryfi_outputs/`.
- `scripts/02-process.py` reads each cached `ocr_text`, runs the validator,
  parses accepted documents, writes JSON to `data/02-results/` and stores a log in `logs/`.

## 3. Project structure

```
.
├── data/                          # gitignored to prevent data leakage
│   ├── 00-inputs/                 #   source PDFs (5 Switch + 1 exclusion test)
│   ├── 01-veryfi_outputs/         #   cached API responses (full JSON + ocr_text.txt)
│   └── 02-results/                #   final structured JSONs
│
├── docs/                          # external documentation (test brief)
├── logs/                          # gitignored - runtime logs
│
├── scripts/                       # pipeline entry points
│   ├── 00-eval_determinism.py     #   stage 0: check Veryfi API determinism
│   ├── 01-fetch_all.py            #   stage 1: call Veryfi API, cache outputs
│   └── 02-process.py              #   stage 2: validate, parse, generate final JSON.
│
├── src/veryfi_invoice_extractor/  # importable package
│   ├── client.py                  #   Veryfi API wrapper with caching
│   ├── parser.py                  #   ocr_text → structured fields
│   ├── paths.py                   #   centralized filesystem paths
│   └── validator.py               #   format detection (exclusion)
│
├── tests/                         # pytest suite (offline for Zero API consumption)
│   ├── conftest.py                #   shared fixtures
│   ├── fixtures/                  #   anonymized ocr_text samples
│   ├── test_client.py             #   cache + credential loading
│   ├── test_parser.py             #   field extractors + line items
│   └── test_validator.py          #   accept/reject logic
│
├── pyproject.toml                 # project metadata, dependencies, tool config
├── uv.lock                        # pinned versions for reproducibility
├── README.md                      # how to install, run, development guideliness
├── METHODOLOGY.md                 # this file
└── LICENSE                        # MIT, consistent with veryfi-python's license
```

## 4. Field mapping

The Switch invoice template only includes four columns at the line-item level (`Description`, `Quantity`, `Rate`, `Amount`), but the test requests six. This mismatch was the resolved as follows, in line with Veryfi's own field semantics
([source](https://faq.veryfi.com/en/articles/5571268-document-data-extraction-fields-explained)):

| Requested field | Mapped to            | Notes                                                                              |
| --------------- | -------------------- | ---------------------------------------------------------------------------------- |
| `description`   | `Description` column | Product or service description (excluding date and price). Multi-line descriptions are stitched together. |
| `quantity`      | `Quantity` column    | Quantity for the line item. Parsed to `float`; supports thousands separator and negative values. |
| `price`         | `Rate` column        | Unit price for the line item.                                                      |
| `total`         | `Amount` column      | Line item total amount, after any deductions.                                      |
| `sku`           | `None` (not included) | Stock Keeping Unit: a unique product identifier. Not present in the Switch template.    |
| `tax_rate`      | `None` (not included) | Per-line tax rate (e.g. 5%, 15%). Not present in the Switch template. |

The two omitted fields are kept in the output schema (with value `null`) so the JSON shape always matches the test's request, regardless of template. The omission is documented centrally as `OMITTED_LINE_FIELDS` inside `parser.py`.


## 5. Field extraction
Each field is extracted by locating a fixed phrase in the template (an "anchor") and reading the value relative to it.

### 5a. Header fields

| Field            | How it is extracted                                                                    |
| ---------------- | -------------------------------------------------------------------------------------- |
| `vendor_name`    | Captured from the footer line `Please make payments to: <name>`                        |
| `vendor_address` | Combines `PO Box <number>` and the `City, ST ZIP` pattern, both anchored by position   |
| `bill_to_name`   | The second non-empty line after the `Invoice No.` anchor                               |
| `invoice_number` | Last number in the row matching `MM/DD/YY MM/DD/YY <digits>` (invoice/due date header) |
| `date`           | First date in the same header row (`MM/DD/YY`)                                         |
| `total`          | The number following `Total USD $`                                                     |

### 5b. Line-item fields

Line items are extracted by scanning the block between the table header (`Description Quantity Rate Amount`) and the `Total USD` line. Each item is identified by a line that ends in three numbers (quantity, rate, amount); any lines in between that do not follow this shape are treated as continuation of the previous description and concatenated back together.

| Field         | How it is extracted                                                                |
| ------------- | ---------------------------------------------------------------------------------- |
| `description` | Text before the three numeric columns; multi-line descriptions are stitched back   |
| `quantity`    | First number of the three at the end of the line                                   |
| `price`       | Second number of the three at the end of the line                                  |
| `total`       | Third number of the three at the end of the line                                   |
| `sku`         | Set to `None` since the Switch template does not include the SKU                   |
| `tax_rate`    | Set to `None` since the Switch template does not include the tax rate              |

## 5. Parsing strategy

The parser is built on regular expressions. The choice was deliberate, for three reasons. The first one is about the nature of the role. A Data Annotations Engineer produces ground truth for supervised models, thus, reproducibility is essential. By construction, regex guarantees that due to its deterministic nature. The second reason is about the data. The Switch template is highly regular across all five documents (same columns, same headers, same footer phrasing). This scenario is suitable for regex as anchors that identify each field are unambiguous and never change.

The third reason is operational. Regex has effectively no cost: no API calls, no inference latency, no external dependencies. For a pipeline that may eventually process millions of documents, this translates is subtantial savings relative to other approaches. The trade-off is that the parser is tightly coupled to the Switch template: it will not work on a different invoice layout. The validator module guards against this, any document that fails the structural checks is rejected  before reaching the parser, so the parser never sees input it cannot handle.

## 6. Format detection (exclusion)

The validator (`src/veryfi_invoice_extractor/validator.py`) decides whether a document is supported. It checks four structural anchors that, together, identify the Switch template uniquely:

- `Invoice Date  Due Date  Invoice No.`
- `Description  Quantity  Rate  Amount`
- `Total  USD`
- `Please make payments to: Switch`

A document is accepted only if **all four** anchors match. The choice is conservative on purpose: in a data pipeline, a false positive (parsing the wrong template and emitting garbage as ground truth) is far more costly than
a false negative (rejecting a document that could have been parsed and flagging it for review). The `missing_anchors()` helper supports debugging by reporting which anchors did not match.

This bilayer design also separates two distinct concerns:

- **Extension filter** (`fetch_all.py`): only `.pdf` files in `data/00-inputs/` reach the API. This is defensive hygiene against
  accidentally submitting non-document files, not the test's exclusion requirement.
- **Content validator** (`validator.py`): the actual exclusion specified by the test. A valid PDF with a different layout is still rejected here.

## 7. Caching strategy

Calls to the Veryfi API are the most expensive step in the pipeline, both in latency and in cost-per-document at scale. `fetch_and_cache` avoids unnecessary calls by writing two files for every processed PDF:

- `<stem>_full.json`: the entire API response (for inspection and debugging).
- `<stem>_ocr.txt`: the isolated `ocr_text` (the parser's only input).

On subsequent runs, the function returns the cached response from disk unless `force_refresh=True` is passed explicitly. This means the parser and validator can be re-run hundreds of times offline against the same inputs, with zero API cost and zero variance in the underlying text, a property that matters both during development and in any production pipeline that re-processes existing documents.

Caching also has a secondary benefit: tests can use anonymized `ocr_text` fixtures (`tests/fixtures/switch_ocr_sample.txt`,
`tests/fixtures/non_switch_ocr.txt`) without ever needing credentials or network access at test time.

## 8. Data confidentiality

Per Veryfi's policy on company-owned data in public repositories, the`data/` directory is fully gitignored. This applies to source PDFs, cached API responses, and the final JSON outputs alike. The `.gitignore` also covers `logs/` to keep runtime traces out of the repository.

The test fixtures under `tests/fixtures/` are committed but contain no real data: `switch_ocr_sample.txt` is a structural anonymization (all identifiers, addresses, account numbers, and location codes have been replaced with placeholders while preserving the template shape), and `non_switch_ocr.txt` is synthetic text that fails every Switch anchor by construction.

## 9. Code quality practices

The project applies the following practices throughout:

- **`uv`** as the project manager. Reproducibility is guaranteed by `uv.lock`, which pins exact transitive versions.
- **`src/` layout** for the package, with `scripts/` reserved for orchestrators that only import from the package.
- **`ruff`** as the linter and formatter.
- **`mypy`** in strict mode for static type checking, with a single override for `veryfi.*`.
- **`logging`** via the standard library, with dual handlers writing to both stdout and `logs/process.log`. Warnings are reserved for documents rejected by the validator; info-level messages report successful processing.
- **`pytest`** with `pytest-cov` for unit tests. The suite contains **25
  tests**, distributed as:
  - `tests/test_client.py` (24% cov): 6 tests covering the cache behavior of `fetch_and_cache` (hit, miss, `force_refresh`) and the `_load_secret` helper.
  - `tests/test_parser.py` (80% cov): 14 tests covering numeric coercion (`to_float`), the anchor-based row extractor (`extract_by_anchor`), and end-to-end parsing against an anonymized `ocr_text` fixture.
  - `tests/test_validator.py` (100% cov): 5 tests covering the accept/reject/missing-anchors behavior of the validator.

  Mocking is done with `unittest.mock.MagicMock` and `pytest.MonkeyPatch`, for efficiency: the tests run entirely offline, without consuming API quota or requiring credentials at test time.
- **Type hints** on every public function. Optional parameters in `fetch_and_cache` are keyword-only (`*` in the signature) to force self-documenting call sites.
- **Module-level compiled regex constants** rather than re-compiling inside loops, both for performance and for grouping all parser-sensitive patterns in one inspectable place.

The parser is organized as a flat module of pure functions rather than a class. There is no per-instance state to manage and no configuration that varies between calls. If the system needed to support multiple invoice templates with selectable behavior, a small class hierarchy (one per template) would become the natural design, but a single template does not warrant it.

## 10. Assumptions

The following assumptions were taken after inspecting the five provided invoices:

- All five PDFs share the Switch invoice template exactly. Headers, column layout, footer phrasing, and date format (`MM/DD/YY`) are identical across the five.
- Numeric values always use US conventions: comma as thousands separator, period as decimal separator. The parser does not handle other notation.
- Currency is always USD. The grand total is preceded by the literal `"Total USD"`, which is used as both an anchor for the total amount and for delimiting the end of the line-item table.
- The `ocr_text` returned by Veryfi for the same PDF is deterministic enough that the parser's regex anchors remain valid across calls. This was verified informally during development using script `00-eval_determinism.py `.
- Line-item descriptions may span multiple lines in the OCR output. A continuation is any line that does not itself end in three numbers.

## 11. Known limitations

The current implementation is intentionally focused on the Switch template. Known limitations include:

- **Embedded numbers in descriptions**: if a description contained a number formatted as `1,234.56` immediately before the quantity column, the regex could mis-attribute it. This case was not observed in the provided samples but is theoretically possible.
- **Locale-dependent formatting** is not supported. Dates are passed through as strings in the `MM/DD/YY` form the template uses.

## 12. Future improvements

With more time, the following improvements would strengthen the solution:

- **Pydantic schemas** for `Invoice` and `LineItem`, replacing the current `dict` output. This would formalize the contract, enable automatic JSON schema generation, and centralize the omission of `sku` and `tax_rate` in the type system rather than as a runtime constant.
- **Multi-template support** via a small `TemplateParser` class hierarchy, with each subclass providing both a `matches()` predicate and a `parse()` implementation. The current validator + parser pair would become the `SwitchInvoiceParser` subclass.
- **A determinism contract test** against the Veryfi API: two consecutive calls on the same PDF should return identical `ocr_text`. This would be marked as an integration test (excluded from the default `pytest` run) to avoid consuming quota on every invocation.
- **CI via GitHub Actions** running `ruff check`, `mypy`, and `pytest` on every push, on every push, initially targeting Linux across multiple Python versions (3.10–3.13). A multi-OS matrix could be added later if platform-specific behavior becomes relevant.

## 13. Exclusion demonstration

The pipeline was tested against an out-of-format document of our own (kept out of the public repository per Veryfi's data policy). The relevant section of the run log is reproduced below as evidence:

```
WARNING  | REJECTED invoice_example_ocr.txt — missing anchors:
           ['Invoice Date\\s+Due Date\\s+Invoice No\\.',
            'Description\\s+Quantity\\s+Rate\\s+Amount',
            'Total\\s+USD',
            'Please make payments to:\\s*Switch']
INFO     | PROCESSED synth-switch_v5-14_ocr.txt → synth-switch_v5-14.json
INFO     | PROCESSED synth-switch_v5-4_ocr.txt  → synth-switch_v5-4.json
INFO     | PROCESSED synth-switch_v5-68_ocr.txt → synth-switch_v5-68.json
INFO     | PROCESSED synth-switch_v5-79_ocr.txt → synth-switch_v5-79.json
INFO     | PROCESSED synth-switch_v5-7_ocr.txt  → synth-switch_v5-7.json
INFO     | Done. Processed: 5 | Rejected: 1
```

The unrelated document fails all four structural anchors and is rejected with a log explaining exactly which anchors are missing. The five Switch invoices are processed normally and their JSON outputs is saved in `data/02-results/`.

## 14. AI assistance disclosure

This project was developed with assistance from a large language model (Claude by Anthropic) for design discussion, code review, and documentation drafting. All architectural and parsing decisions were authored and reviewed by me.

---

*Juan David Rengifo Castro · May 2026*