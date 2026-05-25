import psycopg2
import json
import gspread
from google.oauth2.service_account import Credentials
from decimal import Decimal
import os

# ── PostgreSQL connection ───────────────────────────────────────
conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    dbname=os.environ["DB_NAME"]
)
cur = conn.cursor()

# ── Clean function ──────────────────────────────────────────────
def clean_value(v):
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (int, float, bool)):
        return v
    return str(v)

# ── Google Sheets Auth ──────────────────────────────────────────
creds = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)

spreadsheet = gc.open_by_key("1IVZOBpCsxDOX7KffsQoXGMvNRw-QA2LcijOhClvHvAE")

# ── Get or create worksheet ─────────────────────────────────────
def get_or_create_worksheet(spreadsheet, name, rows=1000, cols=30):
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)

# ── Run query → specific sheet ──────────────────────────────────
def run_query_to_sheet(query, sheet_name):
    cur.execute(query)

    headers = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    rows_clean = [[clean_value(cell) for cell in row] for row in rows]

    ws = get_or_create_worksheet(spreadsheet, sheet_name)
    ws.clear()
    ws.update("A1", [headers] + rows_clean)

# ── QUERY 1 → EsewaOrderHourly ──────────────────────────────────
run_query_to_sheet(
    """
    SELECT *
    FROM public."Esewa_Order";
    """,
    "EsewaOrderHourly"
)

# ── QUERY 2 → PaymentMethodOrderDOD ─────────────────────────────
run_query_to_sheet(
    """
    SELECT *
    FROM public."payment2023_modified";
    """,
    "PaymentMethodOrderDOD"
)

# ── Close DB connection ─────────────────────────────────────────
cur.close()
conn.close()
