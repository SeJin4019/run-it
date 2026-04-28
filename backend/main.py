from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth, database
from database import engine, get_db

# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Run-it API")

# CORS 설정 (Vue 프론트엔드 연결용)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://sejin4019.github.io",
    "https://SeJin4019.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 명시적으로 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # 백엔드 콘솔에 에러 출력
    traceback.print_exc()
    # CORS 헤더를 포함한 500 에러 반환
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error: " + str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )


# --- 인증 API ---
@app.post("/api/auth/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password, name=user.name, region=user.region)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login")
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not auth.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다.")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "friends": user.friends
        }
    }

# --- 유저 API ---
@app.get("/api/users", response_model=List[schemas.User])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/api/users/add-friend")
def add_friend(user_id: int, friend_email: str, db: Session = Depends(get_db)):
    # 본인 확인
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 추가할 친구 확인
    friend = db.query(models.User).filter(models.User.email == friend_email).first()
    if not friend:
        raise HTTPException(status_code=404, detail="해당 이메일의 사용자를 찾을 수 없습니다.")
    
    if friend.id == user_id:
        raise HTTPException(status_code=400, detail="자기 자신은 친구로 추가할 수 없습니다.")
    
    # 친구 목록 업데이트
    current_friends = list(user.friends) if user.friends else []
    if friend.id in current_friends:
        raise HTTPException(status_code=400, detail="이미 친구로 등록된 사용자입니다.")
    
    current_friends.append(friend.id)
    user.friends = current_friends
    db.commit()
    
    return {"message": f"{friend.name}님을 친구로 추가했습니다.", "friend": friend}

# --- 코스 API ---
@app.get("/api/courses", response_model=List[schemas.Course])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(models.Course).all()
    # 작성자 이름을 함께 반환하기 위해 처리
    result = []
    for c in courses:
        course_data = schemas.Course.from_orm(c)
        course_data.author_name = c.author.name if c.author else "익명"
        result.append(course_data)
    return result

@app.post("/api/courses", response_model=schemas.Course)
def create_course(course: schemas.CourseCreate, user_id: int, db: Session = Depends(get_db)):
    db_course = models.Course(**course.dict(), author_id=user_id)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.delete("/api/courses/{course_id}")
def delete_course(course_id: int, user_id: int, db: Session = Depends(get_db)):
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
    if db_course.author_id != user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    
    db.delete(db_course)
    db.commit()
    return {"message": "코스가 삭제되었습니다."}

# --- 러닝 기록 API ---
@app.get("/api/records/{user_id}", response_model=List[schemas.Record])
def get_user_records(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Record).filter(models.Record.user_id == user_id).all()

@app.post("/api/records", response_model=schemas.Record)
def create_record(record: schemas.RecordCreate, user_id: int, db: Session = Depends(get_db)):
    db_record = models.Record(**record.dict(), user_id=user_id)
    db.add(db_record)
    
    # 신발 마일리지 업데이트
    if record.shoe_id:
        db_shoe = db.query(models.Shoe).filter(models.Shoe.id == record.shoe_id).first()
        if db_shoe:
            db_shoe.total_km += record.distance
            
    db.commit()
    db.refresh(db_record)
    return db_record

# --- 신발 관리 API ---
@app.get("/api/shoes/{user_id}", response_model=List[schemas.Shoe])
def get_user_shoes(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Shoe).filter(models.Shoe.user_id == user_id).all()

@app.post("/api/shoes", response_model=schemas.Shoe)
def create_shoe(shoe: schemas.ShoeCreate, user_id: int, db: Session = Depends(get_db)):
    db_shoe = models.Shoe(**shoe.dict(), user_id=user_id)
    db.add(db_shoe)
    db.commit()
    db.refresh(db_shoe)
    return db_shoe

@app.patch("/api/shoes/{shoe_id}", response_model=schemas.Shoe)
def update_shoe_status(shoe_id: int, is_active: bool, db: Session = Depends(get_db)):
    db_shoe = db.query(models.Shoe).filter(models.Shoe.id == shoe_id).first()
    if not db_shoe:
        raise HTTPException(status_code=404, detail="신발을 찾을 수 없습니다.")
    db_shoe.is_active = is_active
    db.commit()
    db.refresh(db_shoe)
    return db_shoe

@app.delete("/api/shoes/{shoe_id}")
def delete_shoe(shoe_id: int, db: Session = Depends(get_db)):
    db_shoe = db.query(models.Shoe).filter(models.Shoe.id == shoe_id).first()
    if not db_shoe:
        raise HTTPException(status_code=404, detail="신발을 찾을 수 없습니다.")
    db.delete(db_shoe)
    db.commit()
    return {"message": "신발이 삭제되었습니다."}

# --- 실시간 위치 공유 API ---
@app.post("/api/live/update")
def update_live_location(user_id: int, lat: float, lng: float, is_active: bool, db: Session = Depends(get_db)):
    db_loc = db.query(models.LiveLocation).filter(models.LiveLocation.user_id == user_id).first()
    if not db_loc:
        db_loc = models.LiveLocation(user_id=user_id, latitude=lat, longitude=lng, is_active=is_active)
        db.add(db_loc)
    else:
        db_loc.latitude = lat
        db_loc.longitude = lng
        db_loc.is_active = is_active
    
    db.commit()
    return {"status": "success"}

@app.get("/api/live/friends")
def get_friends_live_locations(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.friends:
        return []
    
    # 5분 이내에 업데이트된 활성 상태의 친구만 조회
    time_threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    
    live_friends = db.query(models.LiveLocation).join(models.User, models.LiveLocation.user_id == models.User.id)\
        .filter(models.LiveLocation.user_id.in_(user.friends))\
        .filter(models.LiveLocation.is_active == True)\
        .filter(models.LiveLocation.last_updated >= time_threshold).all()
    
    result = []
    for loc in live_friends:
        result.append({
            "user_id": loc.user_id,
            "name": loc.user.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "last_updated": loc.last_updated
        })
    return result

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
