import os

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

try:
    from dotenv import load_dotenv
    # Explicit path: resolve .env next to this file, not relative to the current
    # working directory (which differs when the app is launched/packaged).
    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
except ImportError:
    pass  # python-dotenv is optional; fall back to real env vars / defaults


def _resolve(path: str) -> str:
    """Make a configured path absolute, relative to the project root."""
    return path if os.path.isabs(path) else os.path.join(_PROJECT_ROOT, path)


DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

DEFAULT_INPUT_DIR  = os.path.join(DESKTOP, "PDF_Input")
DEFAULT_OUTPUT_DIR = os.path.join(DESKTOP, "LEDES_Output")

# ── Google Drive ingestion (sources/gdrive.py) ────────────────────────────────
# OAuth desktop-app client secret. Two ways to provide it (first one wins):
#   1) Put GDRIVE_CLIENT_ID + GDRIVE_CLIENT_SECRET in .env (no file needed).
#   2) Point GDRIVE_CREDENTIALS_FILE at the credentials.json from Google Cloud.
# Keep either out of git (see .gitignore).
GDRIVE_CLIENT_ID     = os.getenv("GDRIVE_CLIENT_ID", "")
GDRIVE_CLIENT_SECRET = os.getenv("GDRIVE_CLIENT_SECRET", "")

# Paths come from .env (or default to the project root) and are made absolute.
GDRIVE_CREDENTIALS_FILE = _resolve(os.getenv("GDRIVE_CREDENTIALS_FILE", "credentials.json"))
GDRIVE_TOKEN_FILE       = _resolve(os.getenv("GDRIVE_TOKEN_FILE", "token.json"))

# Full Drive scope: we list + download PDFs and then MOVE processed files into
# a "Done" subfolder, which requires write access.
GDRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

# ID of the Drive folder that holds incoming invoice PDFs. Take it from the
# folder URL: https://drive.google.com/drive/folders/<THIS_PART>
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")

# After successful conversion, files are moved into this subfolder (created on
# demand). Files there are no longer listed, so "Fetch new" never reprocesses
# them.
GDRIVE_DONE_FOLDER_NAME = "Done"

# ── Law firm configuration (edit for your firm) ───────────────────────────────
LAW_FIRM_NAME      = "IMP"
LAW_FIRM_ADDRESS_1 = "Beneficiary Name: IMP Legal Kft."
LAW_FIRM_ADDRESS_2 = "Beneficiary Address: Hungary, 1137 Budapest, Szent Istvan korut 18 2/3"
LAW_FIRM_CITY      = "Budapest"
LAW_FIRM_STATE     = ""
LAW_FIRM_POSTCODE  = "1137"
LAW_FIRM_COUNTRY   = "HU"
ACCOUNT_TYPE       = "O"

# Default task code per matter family (used when no specific match)
DEFAULT_TASK_CODES = {
    "patent":     "PA499",   # Office Action Attorney Fees
    "litigation": "L120",    # Analysis/Strategy
    "trademark":  "TR799",   # Other Trademark Prosecution
}
DEFAULT_TASK_CODE = DEFAULT_TASK_CODES["patent"]  # backwards-compatible default

# Matter family detection by invoice description / RE: line
# First match wins; defaults to "patent" if nothing matches.
MATTER_FAMILY_RULES = [
    (r"\b(trademark|service\s*mark|\bTM\b|madrid\s*protocol|товарн\w*\s*знак)\b", "trademark"),
    # Pure litigation (court enforcement / lawsuit) without IP prosecution context
    (r"\b(enforcement\s*action|lawsuit|civil\s*action|breach\s*of\s*contract)\b", "litigation"),
    # Patent (default catch-all for opposition / appeal / PCT / national phase)
    (r"\b(patent|PCT|EP\d|national\s*phase|opposition|appeal|examination|prosecution)\b", "patent"),
]

# Roche Patent Task Codes — regex → PA code (most specific first)
ROCHE_PATENT_TASK_RULES = [
    # Opposition & Appeal (Proceedings)
    (r"\b(opposition|appeal|court\s*hearing|appellate|proceeding|hearing)\b", "PA630"),
    (r"\b(notice\s*of\s*opposition|filing\s*opposition|notice\s*of\s*appeal)\b", "PA650"),
    # Grant & Validation
    (r"\b(notice\s*of\s*allowance|certificate\s*of\s*grant)\b", "PA699"),
    (r"\b(grant\b|granted|issued\s*patent)\b", "PA699"),
    (r"\b(validation|validating)\b", "PA360"),
    # Special prosecution variants
    (r"\b(divisional|continuation|continuation-in-part|\bCIP\b)\b", "PA350"),
    (r"\b(SPC\b|\bPTE\b|patent\s*term\s*extension|supplementary\s*protection)\b", "PA399"),
    (r"\bdesign\s*patent\b", "PA330"),
    # Examination & Prosecution
    (r"\b(IDS\b|information\s*disclosure\s*statement)\b", "PA610"),
    (r"\b(office\s*action|examination|examining|requesting\s*examination|response\s*to.*office)\b", "PA499"),
    # Filing
    (r"\b(national\s*phase|national\s*/?\s*regional)\b", "PA510"),
    (r"\b(\bPCT\b|regional\s*application|pct\s*regional)\b", "PA520"),
    (r"\b(priority|provisional)\b", "PA310"),
    # Pre-filing
    (r"\b(novelty\s*search|prior\s*art|patentability)\b", "PA220"),
    (r"\b(\bFTO\b|freedom\s*to\s*operate|3rd\s*party\s*IP)\b", "PA230"),
    (r"\b(drafting\s*specification|draft\w*\s+.*application|drafting\s+claims)\b", "PA240"),
    # Other
    (r"\b(licens|assignment|transaction)\w*\b", "PA740"),
    (r"\b(watch|monitoring|status\s*check)\b", "PA299"),
]

# Roche Litigation Task Codes
ROCHE_LITIGATION_TASK_RULES = [
    # Appeal
    (r"\bappellate\s*(motion|submission)\b", "L510"),
    (r"\bappellate\s*brief|appeal\s*brief\b", "L520"),
    (r"\boral\s*argument\b", "L530"),
    # Trial
    (r"\b(post.?trial|after\s*trial)\b", "L460"),
    (r"\benforcement\b", "L470"),
    (r"\b(trial\s*attendance|hearing\s*attendance|attending\s*trial)\b", "L450"),
    (r"\b(expert\s*witness)\b", "L420"),
    (r"\b(fact\s*witness)\b", "L410"),
    (r"\b(trial\s*preparation|trial\s*support)\b", "L440"),
    (r"\b(written\s*motion|trial\s*motion|trial\s*submission)\b", "L430"),
    # Discovery
    (r"\b(written\s*discovery|interrogator)\b", "L310"),
    (r"\b(document\s*production)\b", "L320"),
    (r"\b(deposition)\b", "L330"),
    (r"\b(expert\s*discovery)\b", "L340"),
    (r"\b(discovery\s*motion)\b", "L350"),
    # Pre-trial pleadings & motions
    (r"\b(preliminary\s*injunction|provisional\s*remed)\b", "L220"),
    (r"\bcourt.{0,15}conference\b", "L230"),
    (r"\b(dispositive\s*motion|summary\s*judgment)\b", "L240"),
    (r"\b(class\s*action|class\s*certification)\b", "L260"),
    (r"\b(pleading|complaint|answer|petition\b)\b", "L210"),
    (r"\b(motion|brief|submission)\b", "L250"),
    # Case Assessment
    (r"\b(settlement|mediat|\bADR\b|negotiat)\b", "L160"),
    (r"\bbudget", "L150"),
    (r"\b(document\s*management|file\s*management|docket|indexing)\b", "L140"),
    (r"\b(expert|consultant)\b", "L130"),
    (r"\b(investigation|fact\s*finding|fact\s*development)\b", "L110"),
    (r"\b(analysis|strategy|review|examin|evaluat|assess|study|studying)\w*\b", "L120"),
]

# Roche Trademark Task Codes
ROCHE_TRADEMARK_TASK_RULES = [
    (r"\b(publication\s*watch|watch\s*service)\b", "TR250"),
    (r"\b(status\s*invest|status\s*check)\b", "TR270"),
    (r"\b(opposition\s*invest|investigat\w*\s*opposition)\b", "TR240"),
    (r"\b(enforcement\s*invest|investigat\w*\s*enforcement)\b", "TR260"),
    (r"\b(knock.?out|preliminary\s*search|registerabil|trademark\s*invest)\b", "TR200"),
    (r"\b(international\s*application|madrid|WIPO)\b", "TR510"),
    (r"\b(domestic.*application|application.*domestic|domestic\s*filing)\b", "TR310"),
    (r"\b(quasi.?judicial|appeal|opposition\s*proceed)\b", "TR440"),
    (r"\b(office\s*action|official\s*communication)\b", "TR430"),
    (r"\b(affidavit|petition|extension|declaration|renewal)\b", "TR410"),
    (r"\b(quasi.?judicial.*international)\b", "TR640"),
    (r"\b(official\s*communication.*international)\b", "TR630"),
    (r"\b(assignment|security\s*interest)\b", "TR730"),
    (r"\b(licens)\w*\b", "TR740"),
]

# Roche Expense Codes — regex → E code (most specific first)
ROCHE_EXPENSE_RULES = [
    # IP-specific
    (r"\b(annuity|maintenance\s*fee|renewal\s*fee|post.?issuance)\b", "E130"),
    (r"\b(late\s*fee|surcharge|extension\s*of\s*time|petition\s*for\s*extension)\b", "E131"),
    (r"\b(translation|translating|перевод)\b", "E125"),
    (r"\b(drawing|draftsman)\b", "E126"),
    (r"\b(patent\s*records|trademark\s*records|file\s*histor|priority\s*document|patent\s*cop)\b", "E127"),
    (r"\b(search\w*|monitor\w*)\b", "E128"),
    # Litigation expenses
    (r"\b(court\s*fee)\b", "E112"),
    (r"\b(subpoena)\b", "E113"),
    (r"\b(witness\s*fee)\b", "E114"),
    (r"\b(deposition\s*transcript)\b", "E115"),
    (r"\b(trial\s*transcript)\b", "E116"),
    (r"\b(trial\s*exhibit)\b", "E117"),
    (r"\b(litigation\s*support)\b", "E118"),
    (r"\b(expert\s*fee|expert\s*charge)\b", "E119"),
    (r"\b(private\s*investigator)\b", "E120"),
    (r"\b(arbitrator|mediator)\b", "E121"),
    (r"\b(local\s*counsel|foreign\s*associate|associate\s*fee)\b", "E122"),
    # Tax
    (r"\b(VAT|\bGST\b|consumption\s*tax|value\s*added\s*tax)\b", "EVAT"),
    # General office expenses
    (r"\b(copying|copy\s*charge|xerox|in.?house\s*cop)\b", "E101"),
    (r"\b(outside\s*print|printing)\b", "E102"),
    (r"\b(word\s*process)\b", "E103"),
    (r"\b(facsimile|\bfax\b)\b", "E104"),
    (r"\b(telephone|phone|call\s*charge)\b", "E105"),
    (r"\b(online\s*research|westlaw|lexis|database\s*charge)\b", "E106"),
    (r"\b(delivery\s*service|courier|FedEx|\bDHL\b)\b", "E107"),
    (r"\b(postage|mailing)\b", "E108"),
    (r"\b(local\s*travel)\b", "E109"),
    (r"\b(travel|out.?of.?town|flight|train|hotel|accommodation)\b", "E110"),
    (r"\b(meals?)\b", "E111"),
    (r"\b(service\s*charge)\b", "E124"),
    # Catch-all official fees
    (r"\b(official\s*(fee|examination\s*fee|filing\s*fee)|filing\s*fee|government\s*fee|gov\.?\s*fee|fee\s*for\s*request)\b", "E129"),
]
DEFAULT_EXPENSE_CODE = "E129"  # default to Official Fees

# UTBMS activity code mapping: regex → A-code (applied to fee items)
# Patterns are tested in order; first match wins.
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
