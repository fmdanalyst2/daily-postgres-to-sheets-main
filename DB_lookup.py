import psycopg2
import os

# connect to the postgreSQL
conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    dbname=os.environ["DB_NAME"]
)

try:
    conn.autocommit = True  # safest for REFRESH
    cur = conn.cursor()

    cur.execute(
        'REFRESH MATERIALIZED VIEW "db_lookup";'
    )

    print("Delivery boy lookup view refreshed successfully!")

except Exception as e:
    print(f"Refresh failed: {e}")

finally:
    cur.close()
    conn.close()
