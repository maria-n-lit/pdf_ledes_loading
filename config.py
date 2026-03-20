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
# Patterns are tested in order; first match wins.
# More specific patterns must come before general ones.
ACTIVITY_CODE_RULES = [
    # A109 - Appear for/attend (hearing with active participation)
    (r"\b(speaking|appear|attend|participat)\w*\b.*\b(hear|trial|court|arbitrat|mediat)", "A109"),
    (r"\b(hear|trial|court|arbitrat|mediat)\w*\b.*\b(speaking|appear|attend|participat)", "A109"),

    # A108 - Communicate (other external: court, registry, authorities)
    (r"\b(filing|fil\w+)\b.*\b(court|registr|authorit|office)\b", "A108"),
    (r"\bserving\s+part", "A108"),
    (r"\b(court|registr|authorit|notary|expert)\b.*\b(filing|submit|send|serv)", "A108"),

    # A105 - Communicate (in firm / internally)
    (r"\binternally\b", "A105"),
    (r"\binternal\s+(call|meet|discuss|conference|deliberat)", "A105"),
    (r"\b(discuss|deliberat)\w*\s+.*\binternally\b", "A105"),

    # A103 - Draft/revise (drafting, amending, modifying documents)
    (r"\b(draft|revis|amend|finaliz)\w*\b", "A103"),
    (r"\bmodifying\s+(brief|document|motion|claim|petition|complaint|response)", "A103"),

    # A102 - Research (legal research, prior art search, analysis)
    (r"\b(research|prior\s*art\s*search)\b", "A102"),
    (r"\banalys\w*\b.*\b(regarding|of|re)\b", "A102"),

    # A101 - Plan and prepare for (preparing for hearing/trial without participation)
    (r"\bprepar\w*\b.*\b(hearing|trial|court|arbitrat|mediat|proceed)\b", "A101"),
    (r"\b(hearing|trial|court|arbitrat|mediat|proceed)\b.*\bprepar\w*\b", "A101"),

    # A110 - Manage data/files
    (r"\b(filing|organiz|index|docket|document\s*manag|manage\s*data|manage\s*file)\w*\b", "A110"),

    # A111 - Other
    (r"\b(travel|flight|train|transport|trip)\b", "A111"),

    # A106 - Communicate (with client) - broad client communication
    (r"\bclient\b", "A106"),
    (r"\b(call|communicat|correspond|meet|discuss|letter|email|telephone|follow\w*\s*up)\b", "A106"),

    # A104 - Review/analyze (standalone, fallback)
    (r"\b(review|analyz|examin|evaluat|assess|inspect|stud)\w*\b", "A104"),
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