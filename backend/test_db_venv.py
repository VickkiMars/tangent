import psycopg2
import os

urls = [
    "postgresql:///tangent_db",
    "postgresql://kami@/tangent_db",
    "postgresql://postgres@/tangent_db",
    "postgresql://postgres:postgres@localhost:5432/tangent_db"
]

for url in urls:
    try:
        conn = psycopg2.connect(url)
        print(f"SUCCESS: {url}")
        conn.close()
    except Exception as e:
        print(f"FAIL {url}: {e}")
