import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "bayansafe"),
        user=os.getenv("DB_USER", "bayan_api"),
        password=os.getenv("DB_PASSWORD", ""),
    )


if __name__ == "__main__":
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT question_id, prompt FROM questions")
        for row in cur.fetchall():
            print(row)