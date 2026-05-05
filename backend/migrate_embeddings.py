import google.generativeai as genai
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import SessionLocal
import models

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def get_embedding(text: str):
    if not text: return None
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error for '{text[:20]}...': {e}")
        return None

def migrate():
    db = SessionLocal()
    courses = db.query(models.Course).filter(models.Course.description_embedding == None).all()
    
    print(f"총 {len(courses)}개의 코스 임베딩 작업을 시작합니다.")
    
    count = 0
    for course in courses:
        emb = get_embedding(course.description)
        if emb:
            course.description_embedding = emb
            count += 1
            if count % 5 == 0:
                db.commit()
                print(f"{count}개 완료...")
    
    db.commit()
    print(f"마이그레이션 완료! 총 {count}개의 코스 임베딩이 업데이트되었습니다.")
    db.close()

if __name__ == "__main__":
    migrate()
