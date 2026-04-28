import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def seed():
    db = SessionLocal()
    # 기존 데이터가 있으면 넘어가기
    if db.query(models.Course).first():
        print("이미 데이터가 존재합니다.")
        return

    # 초기 유저 생성
    user = models.User(
        email="runner@example.com",
        name="런린이",
        hashed_password="hashed_password_placeholder"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 초기 코스 데이터
    courses = [
        models.Course(
            name="한강 시민공원 망원지구 코스",
            location="서울 마포구",
            distance=5.2,
            elevation=10,
            difficulty="쉬움",
            parking="유료 주차장 이용",
            description="한강을 보며 달릴 수 있는 탁 트인 코스입니다. 평탄하여 초보자에게 추천합니다.",
            image="https://images.unsplash.com/photo-1513594422441-24424ade8773?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
            path=[[37.555, 126.891], [37.550, 126.895], [37.545, 126.900]],
            author_id=user.id
        ),
        models.Course(
            name="남산 둘레길 코스",
            location="서울 용산구",
            distance=7.5,
            elevation=120,
            difficulty="보통",
            parking="남산도서관 주차장",
            description="서울의 전경을 감상하며 뛸 수 있는 업다운이 있는 코스입니다.",
            image="https://images.unsplash.com/photo-1502126324834-38f8e02d7160?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
            path=[[37.551, 126.988], [37.553, 126.991], [37.555, 126.994]],
            author_id=user.id
        )
    ]
    
    for c in courses:
        db.add(c)
    
    db.commit()
    print("초기 데이터 시딩 완료!")

if __name__ == "__main__":
    seed()
