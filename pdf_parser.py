"""
PDF Invoice Parser.
Extracts billing data from PDF invoices using text analysis and regex patterns.
"""

import re
import pdfplumber
from dataclasses import dataclass, field


@dataclass
class LineItem:
    date: str = ""
    description: str = ""
    timekeeper: str = ""
    timekeeper_first: str = ""
    timekeeper_last: str = ""
    task_code: str = ""
    activity_code: str = ""
    expense_code: str = ""
    unit_cost: float = 0.0
    units: float = 1.0
    adjustment: float = 0.0
    total: float = 0.0
    item_type: str = "F"  # F=Fee, E=Expense


@dataclass
class InvoiceData:
    invoice_number: str = ""
    invoice_date: str = ""
    client_id: str = ""
    matter_id: str = ""
    client_matter_id: str = ""
    law_firm_matter_id: str = ""
    description: str = ""
    total: float = 0.0
    # Extended fields
    invoice_currency: str = ""
    law_firm_id: str = ""
    client_name: str = ""
    client_tax_id: str = ""
    client_postcode: str = ""
    client_country: str = ""
    matter_name: str = ""
    po_number: str = ""
    billing_start_date: str = ""
    billing_end_date: str = ""
    line_items: list[LineItem] = field(default_factory=list)
    source_file: str = ""


# ── Regex patterns ─────────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    r"\b(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})\b",
    r"\b(\d{4}[./\-]\d{1,2}[./\-]\d{1,2})\b",
    r"\b(\w+ \d{1,2},?\s*\d{4})\b",
]

_INVOICE_NUM_PATTERNS = [
    r"[№#]\s*([A-Z][A-Z0-9\-]{3,})",
    r"Number:\s*([A-Za-z][A-Za-z0-9\-]+)",
    r"(?:invoice|инвойс)[^\w]*(?:no\.?|num(?:ber)?|#|№)?[^\w]*([A-Z0-9\-]+)",
]

_ISSUE_DATE_PATTERNS = [
    r"[Ii]ssue\s*date:?\s*(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4})",
    r"[Ii]ssue\s*date:?\s*(\w+\s+\d{1,2},?\s*\d{4})",
]

_TOTAL_PATTERNS = [
    r"Total\s+amount\s+due:?\s*[\$€£]?\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)",
    r"(?:total|итого|всего|amount\s+due|к\s+оплате)[^\d]*[\$€£]?\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)",
]

_LINE_AMOUNT = re.compile(r"[\$€£]?\s*(\d[\d,]*\.\d{2})")
_EXPENSE_KW  = re.compile(r"\b(expense|расход|disbursement|копир|print|travel|поездка|filing|пошлин)\b", re.I)
_OUR_REF     = re.compile(r"[Oo]ur\s+ref:?\s*([A-Z0-9\-]+)", re.I)
_YOUR_REF    = re.compile(r"[Yy]our\s+ref:?\s*([A-Z0-9\-]+)", re.I)
_LAW_FIRM_ID = re.compile(r"Tax\s*[#№]\s*([\d\-]+)")
_CURRENCY    = re.compile(r"\b(USD|EUR|GBP|CHF|HUF|RUB|JPY|CNY)\b")
_VAT_ID      = re.compile(r"VAT\s*ID:\s*([A-Z]{2}[\s\d]+)", re.I)
_POSTCODE_CITY = re.compile(r"\b(\d{4,5})[,\s]+[A-Z][a-z]")
_RE_LINE     = re.compile(r"RE:\s*(.+)", re.I)
_DATE_CELL   = re.compile(r"^\d{1,2}[./]\d{1,2}[./]\d{4}$")
_SKIP_ROW    = re.compile(r"^(Sub-Total|Total|Disbursement|Professional\s+Services|Date\s+Timekeeper)", re.I)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _first_match(patterns: list[str], text: str, flags=re.I) -> str:
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            return m.group(1).strip()
    return ""


def _normalize_date(raw: str) -> str:
    """Convert various date formats to YYYYMMDD."""
    raw = raw.strip().rstrip(".,")

    m = re.match(r"(\d{1,2})[./\-](\d{1,2})[./\-](\d{2,4})$", raw)
    if m:
        d, mo, y = m.groups()
        y = ("20" + y) if len(y) == 2 else y
        return f"{y}{int(mo):02d}{int(d):02d}"

    m = re.match(r"(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})$", raw)
    if m:
        y, mo, d = m.groups()
        return f"{y}{int(mo):02d}{int(d):02d}"

    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
        "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
    }
    m = re.match(r"(\w+)\s+(\d{1,2}),?\s*(\d{4})", raw, re.I)
    if m:
        mon_str, d, y = m.groups()
        mo = months.get(mon_str[:3].lower(), 1)
        return f"{y}{mo:02d}{int(d):02d}"

    return raw


def _parse_amount(s: str) -> float:
    try:
        cleaned = re.sub(r"[^\d.]", "", s.replace(",", "."))
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def _ref_to_ids(our_ref: str) -> tuple[str, str]:
    """'IMP-1464-26-04' → (client_id='IMP-1464', matter_id='IMP-1464-26')."""
    parts = our_ref.split("-")
    client_id = "-".join(parts[:2]) if len(parts) >= 2 else our_ref
    matter_id = "-".join(parts[:3]) if len(parts) >= 3 else our_ref
    return client_id, matter_id


def _country_code(name: str) -> str:
    from config import COUNTRY_CODES
    return COUNTRY_CODES.get(name.strip().lower(), name.strip().upper()[:3])


# ── Table extraction via word positions ───────────────────────────────────────

_Y_TOLERANCE = 4   # pixels — same row tolerance


def _group_by_row(words: list[dict]) -> dict[float, list[dict]]:
    """Group pdfplumber word dicts by y-coordinate row (with tolerance)."""
    rows: dict[float, list[dict]] = {}
    for w in words:
        placed = False
        for row_y in rows:
            if abs(w["top"] - row_y) <= _Y_TOLERANCE:
                rows[row_y].append(w)
                placed = True
                break
        if not placed:
            rows[w["top"]] = [w]
    return rows


def _extract_items_from_page(page, invoice_date: str) -> list[LineItem]:
    """
    Extract line items from one pdfplumber page using word x/y positions.

    Column layout (derived from header words):
      Date        | Timekeeper           | Description … | Unit | Qty | Tariff | Total
      x ≈ 30-80   | x ≈ 80-(desc_x-1)   | desc_x…       | …    | …   | …      | …
    """
    words = page.extract_words()
    if not words:
        return []

    # Find the header row containing "Timekeeper"
    tk_header = next((w for w in words if w["text"] == "Timekeeper"), None)
    if not tk_header:
        return []

    header_y    = tk_header["top"]
    header_row  = {w["text"]: w["x0"] for w in words if abs(w["top"] - header_y) <= _Y_TOLERANCE}

    tk_x_start  = header_row.get("Timekeeper", 80)
    # date/timekeeper boundary: timekeeper header minus a small margin
    # (first-name words start a bit before the header text)
    date_tk_boundary = tk_x_start - 20          # e.g. 74 for header at 94
    # timekeeper/description boundary: timekeeper header plus fixed offset
    # Chosen so that "Gizatullin" (x≈112) stays in TK and "Studying"/"Registration"
    # (x≈152) move to description. The magic number 50 comes from the observed layout.
    tk_desc_boundary = tk_x_start + 50          # e.g. 144 for header at 94

    # Collect data words below the header line
    data_words = [w for w in words if w["top"] > header_y + _Y_TOLERANCE]

    rows_map = _group_by_row(data_words)
    items: list[LineItem] = []

    for row_y in sorted(rows_map.keys()):
        row = sorted(rows_map[row_y], key=lambda w: w["x0"])

        # Split into columns by x-position
        date_words = [w["text"] for w in row if w["x0"] < date_tk_boundary]
        tk_words   = [w["text"] for w in row if date_tk_boundary <= w["x0"] < tk_desc_boundary]
        desc_words = [w["text"] for w in row if tk_desc_boundary <= w["x0"] < header_row.get("Unit", 370) - 5]
        amt_texts  = [w["text"] for w in row if w["x0"] >= header_row.get("Unit", 370) - 5]

        date_str = date_words[0] if date_words else ""

        if date_str and _DATE_CELL.match(date_str):
            # Skip totals / header echoes
            if _SKIP_ROW.search(" ".join(desc_words)):
                continue

            # Parse amounts: skip non-numeric unit type words (e.g., "hour")
            amounts = [_parse_amount(t) for t in amt_texts
                       if re.match(r"[\d,]+\.?\d*", t) and _parse_amount(t) > 0]
            if len(amounts) < 2:
                continue

            item = LineItem()
            item.date = _normalize_date(date_str)

            parts = tk_words
            item.timekeeper_first = parts[0] if parts else ""
            item.timekeeper_last  = parts[1] if len(parts) > 1 else ""
            item.timekeeper       = " ".join(parts)

            item.description = " ".join(desc_words)[:200]

            if len(amounts) >= 3:
                item.units     = amounts[-3]
                item.unit_cost = amounts[-2]
                item.total     = amounts[-1]
            else:
                item.unit_cost = amounts[-2]
                item.total     = amounts[-1]
                item.units     = round(item.total / item.unit_cost, 4) if item.unit_cost else 1.0

            item.item_type = "E" if _EXPENSE_KW.search(" ".join(amt_texts + desc_words)) else "F"
            items.append(item)

        elif not date_str and items:
            # Continuation row: no date → belongs to the last item
            last = items[-1]
            if tk_words and not last.timekeeper_last:
                last.timekeeper_last = tk_words[0]
                last.timekeeper = f"{last.timekeeper_first} {last.timekeeper_last}".strip()
            if desc_words:
                extra = " ".join(desc_words)
                last.description = (last.description + " " + extra).strip()[:200]

    return items


def _extract_items_fallback(pages_text: list[str], invoice_date: str) -> list[LineItem]:
    """Generic fallback: scan every text line for amount patterns."""
    items: list[LineItem] = []
    full_text = "\n".join(pages_text)

    for raw_line in full_text.splitlines():
        line = raw_line.strip()
        if len(line) < 5:
            continue
        amounts = _LINE_AMOUNT.findall(line)
        if not amounts:
            continue
        if re.search(r"^(total|итого|всего|subtotal|tax|ндс|balance)", line, re.I):
            continue

        item = LineItem()
        item.item_type = "E" if _EXPENSE_KW.search(line) else "F"

        date_m = re.search(r"(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}|\d{4}[./\-]\d{2}[./\-]\d{2})", line)
        item.date = _normalize_date(date_m.group(1)) if date_m else invoice_date

        parsed = [_parse_amount(a) for a in amounts]
        item.total = parsed[-1]
        if len(parsed) >= 2:
            item.unit_cost = parsed[-2]
            item.units = round(item.total / item.unit_cost, 4) if item.unit_cost else 1.0
        else:
            item.unit_cost = item.total
            item.units = 1.0

        desc = line
        for a in amounts:
            desc = desc.replace(a, "")
        if date_m:
            desc = desc.replace(date_m.group(1), "")
        desc = re.sub(r"[\$€£]", "", desc).strip(" |,-")
        item.description = re.sub(r"\s{2,}", " ", desc)[:200]

        if item.total > 0 and item.description:
            items.append(item)

    return items


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_pdf(filepath: str) -> InvoiceData:
    """Parse a PDF invoice file and return structured InvoiceData."""
    invoice = InvoiceData(source_file=filepath)

    with pdfplumber.open(filepath) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]

        # Extract line items inside the same context (word positions)
        items: list[LineItem] = []
        for page in pdf.pages:
            items.extend(_extract_items_from_page(page, ""))
        invoice.line_items = items

    full_text = "\n".join(pages_text)
    flat = re.sub(r"[ \t]+", " ", full_text)   # collapse spaces, keep newlines

    # ── Invoice number ────────────────────────────────────────────────────────
    invoice.invoice_number = _first_match(_INVOICE_NUM_PATTERNS, flat) or "INV001"

    # ── Invoice date (prefer "Issue date:") ───────────────────────────────────
    issue_raw = _first_match(_ISSUE_DATE_PATTERNS, flat)
    if issue_raw:
        invoice.invoice_date = _normalize_date(issue_raw)
    else:
        all_dates = []
        for pat in _DATE_PATTERNS:
            all_dates.extend(re.findall(pat, flat, re.I))
        invoice.invoice_date = _normalize_date(all_dates[0]) if all_dates else ""

    # ── Our ref → CLIENT_ID + LAW_FIRM_MATTER_ID ─────────────────────────────
    ref_m = _OUR_REF.search(flat)
    if ref_m:
        invoice.client_id, invoice.law_firm_matter_id = _ref_to_ids(ref_m.group(1))
    else:
        invoice.client_id = "CLIENT"
        invoice.law_firm_matter_id = ""

    # ── Your ref → PO_NUMBER + CLIENT_MATTER_ID ──────────────────────────────
    your_ref_m = _YOUR_REF.search(flat)
    if your_ref_m:
        invoice.po_number = your_ref_m.group(1).strip()
        invoice.client_matter_id = invoice.po_number
    else:
        invoice.client_matter_id = f"{invoice.client_id}-{invoice.law_firm_matter_id}"

    invoice.matter_id = invoice.law_firm_matter_id

    # ── Invoice description from RE: line ─────────────────────────────────────
    re_m = _RE_LINE.search(flat)
    if re_m:
        invoice.description = re_m.group(1).strip()[:200]
    else:
        for line in flat.splitlines():
            line = line.strip()
            if len(line) > 10 and not re.search(r"^\d", line):
                invoice.description = line[:100]
                break

    # ── Invoice total ─────────────────────────────────────────────────────────
    total_str = _first_match(_TOTAL_PATTERNS, flat)
    invoice.total = _parse_amount(total_str) if total_str else 0.0

    # ── Law firm ID (Tax #) ───────────────────────────────────────────────────
    lf_m = _LAW_FIRM_ID.search(flat)
    invoice.law_firm_id = lf_m.group(1) if lf_m else ""

    # ── Currency ──────────────────────────────────────────────────────────────
    cur_m = _CURRENCY.search(flat)
    invoice.invoice_currency = cur_m.group(1) if cur_m else "USD"

    # ── Client VAT / tax ID ───────────────────────────────────────────────────
    vat_m = _VAT_ID.search(flat)
    if vat_m:
        invoice.client_tax_id = re.sub(r"\s+", "", vat_m.group(1)).strip()

    # ── Client postcode ───────────────────────────────────────────────────────
    pc_m = _POSTCODE_CITY.search(flat)
    invoice.client_postcode = pc_m.group(1) if pc_m else ""

    # ── Client country (line just before "Attn:") ─────────────────────────────
    lines = flat.splitlines()
    for idx, ln in enumerate(lines):
        if re.search(r"Attn:|[Aa]ttention:", ln):
            for j in range(idx - 1, max(0, idx - 5), -1):
                candidate = lines[j].strip()
                if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$", candidate):
                    invoice.client_country = _country_code(candidate)
                    break
            break

    # ── Fallback if no items found via positions ───────────────────────────────
    if not invoice.line_items:
        invoice.line_items = _extract_items_fallback(pages_text, invoice.invoice_date)

    if not invoice.line_items and invoice.total:
        invoice.line_items.append(LineItem(
            date=invoice.invoice_date,
            description=invoice.description or "Legal Services",
            unit_cost=invoice.total,
            units=1.0,
            total=invoice.total,
        ))

    if not invoice.total:
        invoice.total = sum(i.total for i in invoice.line_items)

    # ── Billing date range ────────────────────────────────────────────────────
    dates = sorted(item.date for item in invoice.line_items if item.date)
    if dates:
        invoice.billing_start_date = dates[0]
        invoice.billing_end_date   = dates[-1]

    return invoice
