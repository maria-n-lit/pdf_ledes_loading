import os

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

DEFAULT_INPUT_DIR  = os.path.join(DESKTOP, "PDF_Input")
DEFAULT_OUTPUT_DIR = os.path.join(DESKTOP, "LEDES_Output")

# ── Law firm configuration (edit for your firm) ───────────────────────────────
LAW_FIRM_NAME      = "IMP"
LAW_FIRM_ADDRESS_1 = "Beneficiary Name: IMP Legal Kft."
LAW_FIRM_ADDRESS_2 = "Beneficiary Address: Hungary, 1137 Budapest, Szent Istvan korut 18 2/3"
LAW_FIRM_CITY      = "Budapest"
LAW_FIRM_STATE     = ""
LAW_FIRM_POSTCODE  = "1137"
LAW_FIRM_COUNTRY   = "HU"
ACCOUNT_TYPE       = "O"

# Default UTBMS task code for line items
DEFAULT_TASK_CODE = "L120"

# UTBMS activity code mapping: regex pattern → code
# Patterns are tested in order; first match wins
ACTIVITY_CODE_RULES = [
    (r"\bresearch\b", "A102"),
    (r"\b(call|communicat|correspond|meet|discuss|letter|email)\b", "A106"),
]

# Timekeeper classification by hourly rate threshold
# Sorted descending: first matching threshold applies
TIMEKEEPER_CLASSIFICATION_RATES = [
    (400, "PT"),   # Partner: rate >= 400
    (200, "AS"),   # Associate: rate >= 200
    (0,   "PL"),   # Paralegal: rate < 200
]

# Country name → ISO 3166-1 alpha-3
COUNTRY_CODES = {
    "switzerland": "CHE", "schweiz": "CHE", "suisse": "CHE",
    "hungary": "HUN", "magyarország": "HUN",
    "germany": "DEU", "deutschland": "DEU",
    "austria": "AUT", "österreich": "AUT",
    "france": "FRA",
    "uk": "GBR", "united kingdom": "GBR", "great britain": "GBR",
    "usa": "USA", "united states": "USA",
    "russia": "RUS", "россия": "RUS",
    "china": "CHN", "japan": "JPN", "india": "IND",
}

# LEDES 1998BI V2 column order
LEDES1998BI_V2_COLUMNS = [
    "INVOICE_DATE",
    "INVOICE_NUMBER",
    "CLIENT_ID",
    "LAW_FIRM_MATTER_ID",
    "INVOICE_TOTAL",
    "BILLING_START_DATE",
    "BILLING_END_DATE",
    "INVOICE_DESCRIPTION",
    "LINE_ITEM_NUMBER",
    "EXP/FEE/INV_ADJ_TYPE",
    "LINE_ITEM_NUMBER_OF_UNITS",
    "LINE_ITEM_ADJUSTMENT_AMOUNT",
    "LINE_ITEM_TOTAL",
    "LINE_ITEM_DATE",
    "LINE_ITEM_TASK_CODE",
    "LINE_ITEM_EXPENSE_CODE",
    "LINE_ITEM_ACTIVITY_CODE",
    "TIMEKEEPER_ID",
    "LINE_ITEM_DESCRIPTION",
    "LAW_FIRM_ID",
    "LINE_ITEM_UNIT_COST",
    "TIMEKEEPER_NAME",
    "TIMEKEEPER_CLASSIFICATION",
    "CLIENT_MATTER_ID",
    "PO_NUMBER",
    "CLIENT_TAX_ID",
    "MATTER_NAME",
    "INVOICE_TAX_TOTAL",
    "INVOICE_NET_TOTAL",
    "INVOICE_CURRENCY",
    "TIMEKEEPER_LAST_NAME",
    "TIMEKEEPER_FIRST_NAME",
    "ACCOUNT_TYPE",
    "LAW_FIRM_NAME",
    "LAW_FIRM_ADDRESS_1",
    "LAW_FIRM_ADDRESS_2",
    "LAW_FIRM_CITY",
    "LAW_FIRM_STATEorREGION",
    "LAW_FIRM_POSTCODE",
    "LAW_FIRM_COUNTRY",
    "CLIENT_NAME",
    "CLIENT_ADDRESS_1",
    "CLIENT_ADDRESS_2",
    "CLIENT_CITY",
    "CLIENT_STATEorREGION",
    "CLIENT_POSTCODE",
    "CLIENT_COUNTRY",
    "LINE_ITEM_TAX_RATE",
    "LINE_ITEM_TAX_TOTAL",
    "LINE_ITEM_TAX_TYPE",
    "INVOICE_REPORTED_TAX_TOTAL",
    "INVOICE_TAX_CURRENCY",
]