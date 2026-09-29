import os
import json
from decimal import Decimal
from datetime import date, datetime

import psycopg2
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# PostgreSQL connection
# ============================================================

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    dbname=os.environ["DB_NAME"],
)

# ============================================================
# Google Sheets connection
# ============================================================

creds = Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"]),
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets"
    ],
)

gc = gspread.authorize(creds)

spreadsheet = gc.open_by_key(os.environ["SHEET_ID"])


# ============================================================
# Clean PostgreSQL values
# ============================================================

def clean_value(value):
    if value is None:
        return ""

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, (int, float, bool)):
        return value

    return str(value)


# ============================================================
# Function to export PostgreSQL query to Google Sheet
# ============================================================

def export_query_to_sheet(query, worksheet_name):

    print(f"Running query for: {worksheet_name}")

    with conn.cursor() as cur:

        cur.execute(query)

        headers = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    print(f"Rows fetched: {len(rows)}")

    rows_clean = [
        [clean_value(cell) for cell in row]
        for row in rows
    ]

    all_values = [headers] + rows_clean

    worksheet = spreadsheet.worksheet(worksheet_name)

    # Clear existing data
    worksheet.clear()

    # Write everything in one batch
    worksheet.update(
        "A1",
        all_values,
        value_input_option="USER_ENTERED"
    )

    print(
        f"Successfully updated '{worksheet_name}' "
        f"with {len(rows)} rows and {len(headers)} columns."
    )


# ============================================================
# Main
# ============================================================

try:

    # --------------------------------------------------------
    # Report 1
    # --------------------------------------------------------

    export_query_to_sheet(
        """
        SELECT *
        FROM public."DODOrderMetrics_city_wise";
        """,
        "DODOrder_city"
    )


    # --------------------------------------------------------
    # Report 2
    # --------------------------------------------------------

    export_query_to_sheet(
        """
        SELECT *
        FROM public.appdau_citywise;
        """,
        "AppDAU_city"
    )


    print("All reports updated successfully.")


finally:

    conn.close()

    print("PostgreSQL connection closed.")
