import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.db import get_connection

def inspect_db():
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [r[0] for r in cur.fetchall()]
            print("Tables found:", tables)
            for t in sorted(tables):
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                cnt = cur.fetchone()[0]
                print(f"  Table '{t}': {cnt} rows")
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}'")
                cols = cur.fetchall()
                print(f"    Columns: {', '.join([c[0] + ' (' + c[1] + ')' for c in cols])}")
                if cnt > 0 and cnt <= 10:
                    cur.execute(f"SELECT * FROM {t} LIMIT 5")
                    rows = cur.fetchall()
                    for row in rows:
                        print(f"      Row: {row}")
        conn.close()
    except Exception as e:
        print("DB inspection error:", e)

if __name__ == "__main__":
    inspect_db()
