import psycopg2

urls = [
    "postgresql:///tangent_db",
    "postgresql://kami@/tangent_db"
]

for url in urls:
    try:
        conn = psycopg2.connect(url)
        print(f"SUCCESS: {url}")
        conn.close()
    except Exception as e:
        print(f"FAIL {url}: {e}")
