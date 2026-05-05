from sqlalchemy import text
from database import engine

def add_column():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE courses ADD COLUMN IF NOT EXISTS description_embedding JSON"))
            print("Column added successfully!")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    add_column()
