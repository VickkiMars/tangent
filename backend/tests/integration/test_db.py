import psycopg2

try:
    conn = psycopg2.connect("dbname=tangent_db user=kami")
    print("SUCCESS: Connected to tablet_db as kami")
    conn.close()
except psycopg2.OperationalError as e:
    print(f"FAILED: Connected to tablet_db as kami. Error: {e}")

try:
    conn = psycopg2.connect("dbname=tangent_db user=postgres")
    print("SUCCESS: Connected to tablet_db as postgres")
    conn.close()
except psycopg2.OperationalError as e:
    print(f"FAILED: Connected to tablet_db as postgres. Error: {e}")

