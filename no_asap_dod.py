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
    dbname=os.environ["DB_NAME"],
    connect_timeout=30

)
cur = conn.cursor()

# Your query
cur.execute("""
    SELECT *
    FROM public."SuggestedMinutesBefore&After5PM";
""")

headers = [desc[0] for desc in cur.description]   # get column names
rows = cur.fetchall()

# ── Clean function ──────────────────────────────────────────────
def clean_value(v):
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return float(v)             # most common & safe choice
    if isinstance(v, (int, float, bool)):
        return v
    return str(v)

rows_clean = [[clean_value(cell) for cell in row] for row in rows]

# ── Google Sheets ───────────────────────────────────────────────
creds = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(os.environ["SHEET_ID"]).worksheet("No_ASAP_DOD")

# Optional: start fresh
sheet.clear()

# Write headers + data in one go (faster & cleaner)
all_values = [headers] + rows_clean
sheet.update("A1", all_values)           # ← better than append + clear

# or if you really prefer append style:
# sheet.append_rows(all_values)

cur.close()
conn.close()
