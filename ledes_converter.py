"""
LEDES 1998BI V2 Converter.
Converts InvoiceData objects to LEDES 1998BI V2 pipe-delimited format.
"""

import os
import re
from config import (
    LEDES1998BI_V2_COLUMNS,
    LAW_FIRM_NAME, LAW_FIRM_ADDRESS_1, LAW_FIRM_ADDRESS_2,
    LAW_FIRM_CITY, LAW_FIRM_STATE, LAW_FIRM_POSTCODE, LAW_FIRM_COUNTRY,
    ACCOUNT_TYPE, DEFAULT_TASK_CODE, ACTIVITY_CODE_RULES,
    TIMEKEEPER_CLASSIFICATION_RATES,
)
from pdf_parser import InvoiceData, LineItem


def _fmt_amount(value: float) -> str:
    return f"{value:.2f}"


def _fmt_units(value: float) -> str:
    return f"{value:.2f}"


def _timekeeper_id(first: str, last: str) -> str:
    if first and last:
        return f"{first[0]}.{last}"
    return first or last or "TK1"


def _timekeeper_name(first: str, last: str) -> str:
    """Return 'Last, First' format as used in LEDES."""
    if first and last:
        return f"{last}, {first}"
    return first or last or ""


def _resolve_activity_code(description: str) -> str:
    """Map line item description to UTBMS activity code."""
    for pattern, code in ACTIVITY_CODE_RULES:
        if re.search(pattern, description, re.I):
            return code
    return ""


def _resolve_classification(unit_cost: float) -> str:
    """Map hourly rate to timekeeper classification."""
    for threshold, classification in TIMEKEEPER_CLASSIFICATION_RATES:
        if unit_cost >= threshold:
            return classification
    return ""


def _fmt_adjustment(value: float) -> str:
    if value == 0.0:
        return "0"
    return f"{value:.2f}"


def _row(invoice: InvoiceData, item: LineItem, line_num: int) -> str:
    first = item.timekeeper_first
    last  = item.timekeeper_last

    fields = {
        "INVOICE_DATE":               invoice.invoice_date,
        "INVOICE_NUMBER":             invoice.invoice_number,
        "CLIENT_ID":                  invoice.client_id,
        "LAW_FIRM_MATTER_ID":         invoice.law_firm_matter_id,
        "INVOICE_TOTAL":              _fmt_amount(invoice.total),
        "BILLING_START_DATE":         invoice.billing_start_date,
        "BILLING_END_DATE":           invoice.billing_end_date,
        "INVOICE_DESCRIPTION":        invoice.description.replace("|", "-"),
        "LINE_ITEM_NUMBER":           str(line_num),
        "EXP/FEE/INV_ADJ_TYPE":       item.item_type,
        "LINE_ITEM_NUMBER_OF_UNITS":  _fmt_units(item.units),
        "LINE_ITEM_ADJUSTMENT_AMOUNT": _fmt_adjustment(item.adjustment),
        "LINE_ITEM_TOTAL":            _fmt_amount(item.total),
        "LINE_ITEM_DATE":             item.date or invoice.invoice_date,
        "LINE_ITEM_TASK_CODE":        item.task_code or DEFAULT_TASK_CODE,
        "LINE_ITEM_EXPENSE_CODE":     item.expense_code,
        "LINE_ITEM_ACTIVITY_CODE":    item.activity_code or _resolve_activity_code(item.description),
        "TIMEKEEPER_ID":              _timekeeper_id(first, last),
        "LINE_ITEM_DESCRIPTION":      item.description.replace("|", "-"),
        "LAW_FIRM_ID":                invoice.law_firm_id,
        "LINE_ITEM_UNIT_COST":        _fmt_amount(item.unit_cost),
        "TIMEKEEPER_NAME":            _timekeeper_name(first, last),
        "TIMEKEEPER_CLASSIFICATION":  _resolve_classification(item.unit_cost),
        "CLIENT_MATTER_ID":           invoice.client_matter_id,
        "PO_NUMBER":                  invoice.po_number,
        "CLIENT_TAX_ID":              invoice.client_tax_id,
        "MATTER_NAME":                invoice.matter_name,
        "INVOICE_TAX_TOTAL":          "",
        "INVOICE_NET_TOTAL":          _fmt_amount(invoice.total),
        "INVOICE_CURRENCY":           invoice.invoice_currency,
        "TIMEKEEPER_LAST_NAME":       last,
        "TIMEKEEPER_FIRST_NAME":      first,
        "ACCOUNT_TYPE":               ACCOUNT_TYPE,
        "LAW_FIRM_NAME":              LAW_FIRM_NAME,
        "LAW_FIRM_ADDRESS_1":         LAW_FIRM_ADDRESS_1,
        "LAW_FIRM_ADDRESS_2":         LAW_FIRM_ADDRESS_2,
        "LAW_FIRM_CITY":              LAW_FIRM_CITY,
        "LAW_FIRM_STATEorREGION":     LAW_FIRM_STATE,
        "LAW_FIRM_POSTCODE":          LAW_FIRM_POSTCODE,
        "LAW_FIRM_COUNTRY":           LAW_FIRM_COUNTRY,
        "CLIENT_NAME":                invoice.client_name,
        "CLIENT_ADDRESS_1":           "",
        "CLIENT_ADDRESS_2":           "",
        "CLIENT_CITY":                "",
        "CLIENT_STATEorREGION":       "",
        "CLIENT_POSTCODE":            invoice.client_postcode,
        "CLIENT_COUNTRY":             invoice.client_country,
        "LINE_ITEM_TAX_RATE":         "",
        "LINE_ITEM_TAX_TOTAL":        "0",
        "LINE_ITEM_TAX_TYPE":         "",
        "INVOICE_REPORTED_TAX_TOTAL": "",
        "INVOICE_TAX_CURRENCY":       "",
    }
    return "|".join(fields[col] for col in LEDES1998BI_V2_COLUMNS)


def convert_to_ledes(invoice: InvoiceData) -> str:
    """Return full LEDES 1998BI V2 file content as a string."""
    lines = [
        "LEDES1998BI V2[]",
        "|".join(LEDES1998BI_V2_COLUMNS) + "[]",
    ]
    for idx, item in enumerate(invoice.line_items, start=1):
        lines.append(_row(invoice, item, idx) + "[]")
    return "\n".join(lines) + "\n"


def save_ledes(invoice: InvoiceData, output_dir: str) -> str:
    """Convert invoice to LEDES 1998BI V2 and save to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(invoice.source_file))[0]
    out_path = os.path.join(output_dir, f"{base}.ledes")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(convert_to_ledes(invoice))
    return out_path