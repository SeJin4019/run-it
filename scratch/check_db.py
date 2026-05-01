import sqlite3
import os

# Render uses PostgreSQL, but local might use SQLite.
# Let's check the environment.
db_url = os.getenv("DATABASE_URL", "sqlite:///./runit.db")
print(f"Database URL: {db_url}")

if "sqlite" in db_url:
    db_path = db_url.replace("sqlite:///", "")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM crews")
            crews = cursor.fetchall()
            print(f"Crews: {crews}")
        except Exception as e:
            print(f"Error: {e}")
        conn.close()
    else:
        print("DB file not found")
else:
    print("PostgreSQL detected, cannot check via script easily without psycopg2")
