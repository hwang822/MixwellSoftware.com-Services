import psycopg2

try:
    conn = psycopg2.connect(
        dbname="authdb",
        user="postgres",
        password="Delanyin@00",
        host="127.0.0.1",
        port="5432"
    )
    print("✅ Connected OK")
    conn.close()
except Exception as e:
    print("❌ ERROR:", e)