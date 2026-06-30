# CLAUDE.md

Guidance for working in this repository.

## What this project does

Desktop app that converts PDF law-firm invoices into the **LEDES 98B**
(`LEDES1998BI V2`) e-billing format. A tkinter GUI batch-processes every PDF in
an input folder and writes one `.ledes` file per invoice to an output folder.

Pipeline: `parse_pdf()` (extract structured data from PDF) →
`convert_to_ledes()` / `save_ledes()` (render LEDES 98B rows).

## Layout

| File | Responsibility |
|------|----------------|
| `main.py` | tkinter GUI; runs conversion on a background thread. Entry point. |
| `pdf_parser.py` | PDF → `InvoiceData`/`LineItem` dataclasses. Regex + word-position table extraction (pdfplumber). |
| `ledes_converter.py` | `InvoiceData` → LEDES 98B text. Resolves UTBMS task/activity/expense codes & timekeeper classification. |
| `config.py` | Default I/O folders, law-firm constants, and all UTBMS code-mapping rule tables. |

## Run / develop

```bash
pip install -r requirements.txt   # pdfplumber, pdfminer.six
python main.py                    # or: make pdf to ledes
```

- Input folder default: `~/Desktop/PDF_Input`; output: `~/Desktop/LEDES_Output`
  (both overridable in the GUI). Defaults live in `config.py`.
- Python 3.10+ (uses `list[...]` / `X | Y` typing, dataclasses).
- A local `.venv` is present; prefer `.venv/bin/python`.

## Lint

```bash
.venv/bin/python -m flake8 *.py
```

`.flake8` config intentionally ignores **E221** (assignments are vertically
aligned on purpose) and relaxes line length to 120. Keep new code lint-clean
and match the existing aligned-assignment style.

**Before every commit, run `.venv/bin/python -m flake8 *.py` and make sure it
exits cleanly (no warnings). Do not commit if flake8 reports any issue — fix
them first.**

## Conventions & gotchas

- **No test suite.** Verify changes by generating a sample invoice PDF and
  running it end-to-end through `parse_pdf` → `save_ledes`, then inspecting the
  `.ledes` output. Do not commit test PDFs or extra deps (e.g. reportlab) — use
  the scratchpad / `.venv` and clean up afterward.
- **Code mapping rules** (task/activity/expense, matter family) are regex tables
  in `config.py`, applied most-specific-first. Extend invoice-classification
  behavior there rather than hardcoding in `ledes_converter.py`.
- **Dates** are normalized to `YYYYMMDD`. `_normalize_date` in `pdf_parser.py`
  defaults to **day-first (DD/MM/YYYY)** and only swaps to US MM/DD when a
  component is unambiguously a day (> 12). Fully ambiguous dates (both ≤ 12) stay
  day-first.
- Parser is layout-sensitive: `_extract_items_from_page` keys off a `Timekeeper`
  header word and fixed x-offsets to split columns. There's a generic
  `_extract_items_fallback` (line-scan) when no positioned table is found.
- Law-firm identity (name/address/account type) is hardcoded in `config.py`;
  edit there for a different firm.