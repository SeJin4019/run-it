from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import datetime
import models, schemas, auth, database
from database import engine, get_db

# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

# 누락된 컬럼 자동 마이그레이션 (Render DB 배포용)
try:
    with engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text("ALTER TABLE live_locations ADD COLUMN IF NOT EXISTS path JSON DEFAULT '[]'::json;"))
        conn.execute(text("ALTER TABLE records ADD COLUMN IF NOT EXISTS shoe_id INTEGER;"))
except Exception as e:
    print("Migration Error:", e)

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
def send_friend_request(user_id: int, friend_email: str, db: Session = Depends(get_db)):
    # 본인 확인
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 추가할 친구 확인
    friend = db.query(models.User).filter(models.User.email == friend_email).first()
    if not friend:
        raise HTTPException(status_code=404, detail="해당 이메일의 사용자를 찾을 수 없습니다.")
    
    if friend.id == user_id:
        raise HTTPException(status_code=400, detail="자기 자신에게는 요청할 수 없습니다.")
    
    # 이미 친구인지 확인
    if friend.id in (user.friends or []):
        raise HTTPException(status_code=400, detail="이미 친구인 사용자입니다.")
        
    # 이미 요청을 보냈는지 확인
    existing = db.query(models.FriendRequest).filter(
        models.FriendRequest.from_user_id == user_id,
        models.FriendRequest.to_user_id == friend.id,
        models.FriendRequest.status == "pending"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 친구 요청을 보낸 상태입니다.")

    new_request = models.FriendRequest(from_user_id=user_id, to_user_id=friend.id)
    db.add(new_request)
    db.commit()
    return {"message": f"{friend.name}님께 친구 요청을 보냈습니다."}

@app.get("/api/users/friend-requests/{user_id}")
def get_pending_requests(user_id: int, db: Session = Depends(get_db)):
    requests = db.query(models.FriendRequest).filter(
        models.FriendRequest.to_user_id == user_id,
        models.FriendRequest.status == "pending"
    ).all()
    
    result = []
    for r in requests:
        result.append({
            "request_id": r.id,
            "from_user_id": r.from_user_id,
            "from_user_name": r.from_user.name,
            "from_user_email": r.from_user.email
        })
    return result

@app.post("/api/users/friend-requests/accept")
def accept_friend_request(request_id: int, db: Session = Depends(get_db)):
    request = db.query(models.FriendRequest).filter(models.FriendRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다.")
    
    # 상호 친구 등록
    from_user = db.query(models.User).filter(models.User.id == request.from_user_id).first()
    to_user = db.query(models.User).filter(models.User.id == request.to_user_id).first()
    
    if from_user and to_user:
        f1 = list(from_user.friends) if from_user.friends else []
        f2 = list(to_user.friends) if to_user.friends else []
        
        if to_user.id not in f1: f1.append(to_user.id)
        if from_user.id not in f2: f2.append(from_user.id)
        
        from_user.friends = f1
        to_user.friends = f2
    
    request.status = "accepted"
    db.commit()
    return {"message": "친구 요청을 수락했습니다."}

@app.post("/api/users/friend-requests/decline")
def decline_friend_request(request_id: int, db: Session = Depends(get_db)):
    request = db.query(models.FriendRequest).filter(models.FriendRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="요청을 찾을 수 없습니다.")
    
    request.status = "declined"
    db.commit()
    return {"message": "친구 요청을 거절했습니다."}

@app.post("/api/users/remove-friend")
def remove_friend(user_id: int, friend_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    current_friends = list(user.friends) if user.friends else []
    if friend_id not in current_friends:
        raise HTTPException(status_code=400, detail="친구 목록에 없는 사용자입니다.")
    
    current_friends.remove(friend_id)
    user.friends = current_friends
    db.commit()
    
    return {"message": "친구 삭제가 완료되었습니다."}

# --- 코스 API ---
@app.get("/api/courses", response_model=List[schemas.Course])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(models.Course).all()
    # 작성자 이름을 수동으로 매핑 (또는 relationship 이용)
    for course in courses:
        if course.author:
            course.author_name = course.author.name
        else:
            course.author_name = "익명"
    return courses

@app.post("/api/courses", response_model=schemas.Course)
def create_course(course: schemas.CourseCreate, user_id: int, db: Session = Depends(get_db)):
    db_course = models.Course(**course.dict(), author_id=user_id)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    # 반환 시 이름 포함
    user = db.query(models.User).filter(models.User.id == user_id).first()
    db_course.author_name = user.name if user else "익명"
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
def update_live_location(data: schemas.LiveLocationUpdate, db: Session = Depends(get_db)):
    db_loc = db.query(models.LiveLocation).filter(models.LiveLocation.user_id == data.user_id).first()
    if not db_loc:
        db_loc = models.LiveLocation(
            user_id=data.user_id, 
            latitude=data.latitude, 
            longitude=data.longitude, 
            path=data.path,
            is_active=data.is_active
        )
        db.add(db_loc)
    else:
        db_loc.latitude = data.latitude
        db_loc.longitude = data.longitude
        db_loc.path = data.path
        db_loc.is_active = data.is_active
    
    db.commit()
    return {"status": "success"}

@app.get("/api/live/friends")
def get_friends_live_locations(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.friends:
        return []
    
    # friends가 JSON으로 저장되어 있으므로 리스트인지 확인
    friend_ids = user.friends
    if isinstance(friend_ids, str):
        import json
        try:
            friend_ids = json.loads(friend_ids)
        except:
            friend_ids = []
            
    if not friend_ids:
        return []
    
    # 5분 이내에 업데이트된 활성 상태의 친구만 조회
    time_threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    
    live_friends = db.query(models.LiveLocation).join(models.User, models.LiveLocation.user_id == models.User.id)\
        .filter(models.LiveLocation.user_id.in_(friend_ids))\
        .filter(models.LiveLocation.is_active == True)\
        .filter(models.LiveLocation.last_updated >= time_threshold).all()
    
    result = []
    for loc in live_friends:
        result.append({
            "user_id": loc.user_id,
            "name": loc.user.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "path": loc.path,
            "last_updated": loc.last_updated
        })
    return result

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
