from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import datetime
import models, schemas, auth, database
from database import engine, get_db
import google.generativeai as genai
import os

# Gemini 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"Gemini API Key loaded: {GEMINI_API_KEY[:5]}***")
else:
    print("Gemini API Key NOT found in environment variables!")

def get_embedding(text: str):
    """텍스트 임베딩 생성"""
    if not GEMINI_API_KEY or not text:
        return None
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding Error: {e}")
        return None

def cosine_similarity(v1, v2):
    """코사인 유사도 계산"""
    if not v1 or not v2: return 0
    import math
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0: return 0
    return dot_product / (mag1 * mag2)

# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)

# DB 스키마 마이그레이션 (필요 시에만 주석 해제하여 실행)
# try:
#     with engine.begin() as conn:
#         ... (기존 마이그레이션 로직)
# except Exception as e:
#     print("Migration Error:", e)

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
            "from_user_email": r.from_user.email,
            "from_user_profile_image": r.from_user.profile_image
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
    friend = db.query(models.User).filter(models.User.id == friend_id).first()
    
    if user:
        f1 = list(user.friends) if user.friends else []
        if friend_id in f1:
            f1.remove(friend_id)
            user.friends = f1
            
    if friend:
        f2 = list(friend.friends) if friend.friends else []
        if user_id in f2:
            f2.remove(user_id)
            friend.friends = f2
            
    db.commit()
    return {"message": "상호 친구 삭제가 완료되었습니다."}
    
    return {"message": "친구 삭제가 완료되었습니다."}

@app.post("/api/users/heartbeat")
def user_heartbeat(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.last_seen = datetime.datetime.utcnow()
        db.commit()
    return {"status": "ok"}

@app.put("/api/users/{user_id}/profile-image", response_model=schemas.User)
def update_profile_image(user_id: int, image_data: schemas.ProfileImageUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.profile_image = image_data.profile_image
    db.commit()
    db.refresh(user)
    return user

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
    # 설명 임베딩 생성
    embedding = get_embedding(course.description)
    db_course = models.Course(**course.dict(), author_id=user_id, description_embedding=embedding)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    # 반환 시 이름 포함
    user = db.query(models.User).filter(models.User.id == user_id).first()
    db_course.author_name = user.name if user else "익명"
    return db_course

@app.get("/api/courses/search")
def search_courses_semantic(query: str, db: Session = Depends(get_db)):
    """Gemini 임베딩 기반 시맨틱 검색"""
    if not query:
        return []
    
    query_embedding = get_embedding(query)
    if not query_embedding:
        # 임베딩 실패 시 일반 텍스트 검색(LIKE)으로 대체
        return db.query(models.Course).filter(models.Course.name.contains(query)).all()
    
    courses = db.query(models.Course).all()
    results = []
    for c in courses:
        if c.description_embedding:
            similarity = cosine_similarity(query_embedding, c.description_embedding)
            # 작성자 이름 매핑
            author_name = c.author.name if c.author else "익명"
            results.append({
                "course": c,
                "author_name": author_name,
                "similarity": similarity
            })
    
    # 유사도 순으로 정렬
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # 상위 10개만 반환 (유사도 0.3 이상 권장)
    return [r for r in results if r["similarity"] > 0.2][:10]

@app.post("/api/courses/{course_id}/like")
def toggle_like_course(course_id: int, user_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
    
    current_likes = list(course.liked_users) if course.liked_users else []
    if user_id in current_likes:
        current_likes.remove(user_id)
    else:
        current_likes.append(user_id)
        
    course.liked_users = current_likes
    db.commit()
    return {"liked_users": current_likes}

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

@app.post("/api/courses/{course_id}/comments", response_model=schemas.Course)
def add_course_comment(course_id: int, comment: dict, db: Session = Depends(get_db)):
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
    
    current_comments = list(db_course.comments) if db_course.comments else []
    current_comments.append(comment)
    db_course.comments = current_comments
    db.commit()
    db.refresh(db_course)
    
    if db_course.author:
        db_course.author_name = db_course.author.name
    else:
        db_course.author_name = "익명"
    return db_course

# --- 러닝 기록 API ---
@app.get("/api/records", response_model=List[schemas.Record])
def get_all_records(db: Session = Depends(get_db)):
    return db.query(models.Record).all()

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
            
    # 소속된 크루의 총 거리 업데이트
    user_crews = db.query(models.CrewMember).filter(
        models.CrewMember.user_id == user_id,
        models.CrewMember.status == "accepted"
    ).all()
    
    for mc in user_crews:
        # 크루 전체 거리 업데이트
        crew = db.query(models.Crew).filter(models.Crew.id == mc.crew_id).first()
        if crew:
            if crew.total_distance is None: crew.total_distance = 0.0
            crew.total_distance += record.distance
        
        # 개인별 크루 기여 거리 업데이트
        if mc.distance is None: mc.distance = 0.0
        mc.distance += record.distance
            
    db.commit()
    db.refresh(db_record)
    return db_record

@app.delete("/api/records/{record_id}")
def delete_record(record_id: int, user_id: int, db: Session = Depends(get_db)):
    db_record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    
    if db_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="자신의 기록만 삭제할 수 있습니다.")

    # 신발 마일리지 차감
    if db_record.shoe_id:
        db_shoe = db.query(models.Shoe).filter(models.Shoe.id == db_record.shoe_id).first()
        if db_shoe:
            db_shoe.total_km = max(0, db_shoe.total_km - db_record.distance)
            
    db.delete(db_record)
    db.commit()
    return {"message": "기록이 삭제되었습니다."}

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
            distance=data.distance,
            pace=data.pace,
            time=data.time,
            path=data.path,
            is_active=data.is_active
        )
        db.add(db_loc)
    else:
        db_loc.latitude = data.latitude
        db_loc.longitude = data.longitude
        db_loc.distance = data.distance
        db_loc.pace = data.pace
        db_loc.time = data.time
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
            "distance": loc.distance,
            "pace": loc.pace,
            "time": loc.time,
            "path": loc.path,
            "last_updated": loc.last_updated
        })
    return result

# --- 크루 API ---
@app.get("/api/crews")
def get_crews(db: Session = Depends(get_db)):
    db_crews = db.query(models.Crew).all()
    result = []
    for crew in db_crews:
        accepted_members = [m for m in crew.members if m.status == "accepted"]
        pending_members = [m for m in crew.members if m.status == "pending"]
        
        # 멤버 정보 매핑 (수락된 멤버)
        members_list = []
        for m in accepted_members:
            if m.user:
                members_list.append({
                    "user_id": m.user.id,
                    "name": m.user.name,
                    "profile_image": m.user.profile_image,
                    "status": m.status,
                    "distance": round(m.distance or 0.0, 2),
                    "joined_at": m.joined_at
                })
        
        # 거리 순으로 멤버 정렬 (크루 내 랭킹)
        members_list.sort(key=lambda x: x['distance'], reverse=True)

        # 신청 중인 멤버 (리더에게만 보여주기 위해 정보 포함)
        pending_list = []
        for m in pending_members:
            if m.user:
                pending_list.append({
                    "user_id": m.user.id,
                    "name": m.user.name,
                    "profile_image": m.user.profile_image,
                    "status": m.status,
                    "joined_at": m.joined_at
                })
        
        result.append({
            "id": crew.id,
            "name": crew.name,
            "description": crew.description,
            "image": crew.image,
            "leader_id": crew.leader_id,
            "total_distance": round(crew.total_distance or 0.0, 2),
            "created_at": crew.created_at,
            "member_count": len(accepted_members),
            "members": members_list,
            "pending_members": pending_list
        })
    
    # 총 거리 순으로 정렬 (랭킹)
    result.sort(key=lambda x: x['total_distance'], reverse=True)
    return result

@app.post("/api/crews")
def create_crew(crew_data: schemas.CrewCreate, user_id: int, db: Session = Depends(get_db)):
    # 1. 크루 생성
    db_crew = models.Crew(
        name=crew_data.name,
        description=crew_data.description,
        image=crew_data.image,
        leader_id=user_id
    )
    db.add(db_crew)
    db.commit()
    db.refresh(db_crew)
    
    # 2. 생성자를 멤버로 추가 (자동 수락)
    member = models.CrewMember(crew_id=db_crew.id, user_id=user_id, status="accepted")
    db.add(member)
    db.commit()
    db.refresh(db_crew)
    
    # 3. 결과 반환 (스키마에 맞춰 수동 매핑)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return {
        "id": db_crew.id,
        "name": db_crew.name,
        "description": db_crew.description,
        "image": db_crew.image,
        "leader_id": db_crew.leader_id,
        "created_at": db_crew.created_at,
        "member_count": 1,
        "members": [{
            "user_id": user.id,
            "name": user.name,
            "profile_image": user.profile_image,
            "joined_at": member.joined_at
        }]
    }

@app.post("/api/crews/{crew_id}/join")
def join_crew(crew_id: int, user_id: int, db: Session = Depends(get_db)):
    existing = db.query(models.CrewMember).filter(
        models.CrewMember.crew_id == crew_id, 
        models.CrewMember.user_id == user_id
    ).first()
    if existing:
        if existing.status == "pending":
            raise HTTPException(status_code=400, detail="이미 가입 신청 중입니다.")
        raise HTTPException(status_code=400, detail="이미 가입된 멤버입니다.")
    
    # 가입 신청 (pending 상태)
    member = models.CrewMember(crew_id=crew_id, user_id=user_id, status="pending")
    db.add(member)
    db.commit()
    return {"message": "가입 신청이 완료되었습니다. 크루장의 승인을 기다려주세요."}

@app.post("/api/crews/{crew_id}/approve/{member_id}")
def approve_crew_member(crew_id: int, member_id: int, leader_id: int, db: Session = Depends(get_db)):
    # 리더 권한 확인
    crew = db.query(models.Crew).filter(models.Crew.id == crew_id).first()
    if not crew or crew.leader_id != leader_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    
    member = db.query(models.CrewMember).filter(
        models.CrewMember.crew_id == crew_id,
        models.CrewMember.user_id == member_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="신청 내역을 찾을 수 없습니다.")
        
    member.status = "accepted"
    db.commit()
    return {"message": "가입 신청이 수락되었습니다."}

@app.post("/api/crews/{crew_id}/kick/{member_id}")
def kick_crew_member(crew_id: int, member_id: int, leader_id: int, db: Session = Depends(get_db)):
    # 리더 권한 확인
    crew = db.query(models.Crew).filter(models.Crew.id == crew_id).first()
    if not crew or crew.leader_id != leader_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    
    if member_id == leader_id:
        raise HTTPException(status_code=400, detail="크루장 자신은 내보낼 수 없습니다.")
        
    member = db.query(models.CrewMember).filter(
        models.CrewMember.crew_id == crew_id,
        models.CrewMember.user_id == member_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="멤버를 찾을 수 없습니다.")
        
    db.delete(member)
    db.commit()
    return {"message": "멤버를 내보냈습니다."}

@app.post("/api/crews/{crew_id}/leave")
def leave_crew(crew_id: int, user_id: int, db: Session = Depends(get_db)):
    crew = db.query(models.Crew).filter(models.Crew.id == crew_id).first()
    if not crew:
        raise HTTPException(status_code=404, detail="크루를 찾을 수 없습니다.")
        
    if crew.leader_id == user_id:
        raise HTTPException(status_code=400, detail="크루장은 탈퇴할 수 없습니다. 크루를 삭제해주세요.")
        
    member = db.query(models.CrewMember).filter(
        models.CrewMember.crew_id == crew_id, 
        models.CrewMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="가입된 크루가 아닙니다.")
    
    db.delete(member)
    db.commit()
    return {"message": "크루에서 탈퇴되었습니다."}

@app.delete("/api/crews/{crew_id}")
def delete_crew(crew_id: int, user_id: int, db: Session = Depends(get_db)):
    crew = db.query(models.Crew).filter(models.Crew.id == crew_id).first()
    if not crew:
        raise HTTPException(status_code=404, detail="크루를 찾을 수 없습니다.")
        
    if crew.leader_id != user_id:
        raise HTTPException(status_code=403, detail="크루 삭제 권한이 없습니다.")
        
    db.delete(crew)
    db.commit()
    return {"message": "크루가 삭제되었습니다."}

@app.get("/api/live/crews/{crew_id}")
def get_crew_live_locations(crew_id: int, db: Session = Depends(get_db)):
    # 크루 멤버 ID 목록 조회
    member_ids = [m.user_id for m in db.query(models.CrewMember).filter(models.CrewMember.crew_id == crew_id).all()]
    if not member_ids:
        return []
        
    time_threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    live_members = db.query(models.LiveLocation).join(models.User, models.LiveLocation.user_id == models.User.id)\
        .filter(models.LiveLocation.user_id.in_(member_ids))\
        .filter(models.LiveLocation.is_active == True)\
        .filter(models.LiveLocation.last_updated >= time_threshold).all()
        
    result = []
    for loc in live_members:
        result.append({
            "user_id": loc.user_id,
            "name": loc.user.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "distance": loc.distance,
            "pace": loc.pace,
            "time": loc.time,
            "path": loc.path,
            "last_updated": loc.last_updated
        })
    return result

# --- 챗봇 API ---
@app.post("/api/chatbot", response_model=schemas.ChatResponse)
def chatbot_response(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    user_name = "러너"
    if request.user_id:
        user = db.query(models.User).filter(models.User.id == request.user_id).first()
        if user:
            user_name = user.name

    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        return {"response": f"안녕하세요 {user_name}님! 현재 챗봇 설정이 완료되지 않았습니다. 관리자에게 문의하여 Gemini API 키를 설정해주세요."}

    try:
        model = genai.GenerativeModel('models/gemini-flash-latest')
        
        # 0. 사용자 메시지 DB 저장
        if request.user_id:
            user_msg = models.ChatMessage(user_id=request.user_id, role="user", content=request.message)
            db.add(user_msg)
            db.commit()

        # 1. 과거 대화 내역 가져오기 (최근 5개)
        history_text = ""
        if request.user_id:
            past_messages = db.query(models.ChatMessage).filter(models.ChatMessage.user_id == request.user_id).order_by(models.ChatMessage.created_at.desc()).limit(5).all()
            # 시간순으로 정렬
            past_messages.reverse()
            if past_messages:
                history_text = "\n[최근 대화 내역]\n"
                for m in past_messages[:-1]: # 현재 메시지 제외
                    role_name = "사용자" if m.role == "user" else "코치"
                    history_text += f"{role_name}: {m.content}\n"

        # 2. RAG: DB에서 관련 코스 정보 검색
        related_courses_text = ""
        query_embedding = get_embedding(request.message)
        if query_embedding:
            all_courses = db.query(models.Course).all()
            scored_courses = []
            for c in all_courses:
                if c.description_embedding:
                    score = cosine_similarity(query_embedding, c.description_embedding)
                    if score > 0.3:
                        scored_courses.append((score, c))
            
            scored_courses.sort(key=lambda x: x[0], reverse=True)
            top_courses = scored_courses[:3]
            
            if top_courses:
                related_courses_text = "\n[참고할 수 있는 DB 내 코스 정보]\n"
                for score, c in top_courses:
                    related_courses_text += f"- 이름: {c.name}, 위치: {c.location}, 거리: {c.distance}km, 난이도: {c.difficulty}, 특징: {c.description}\n"

        # 3. 시스템 프롬프트 설정
        system_instruction = f"""
        당신은 'Run-it' 이라는 러닝 앱의 친절하고 전문적인 AI 러닝 코치입니다.
        사용자의 이름은 {user_name}입니다.
        
        이전 대화 내역([최근 대화 내역])이 있다면 흐름을 이어가며 답변하세요.
        제공된 [참고할 수 있는 DB 내 코스 정보]가 있다면 이를 활용하여 답변하세요. 
        사용자의 질문에 대해 러닝, 건강, 운동 계획, 동기 부여와 관련된 조언을 제공하세요.
        답변은 친절하고 격려하는 어조로 한국어로 작성하세요.
        답변 끝에는 항상 러닝을 응원하는 짧은 문구를 덧붙여주세요.
        """
        
        prompt = system_instruction + history_text + related_courses_text + "\n\n현재 질문: " + request.message
        
        response = model.generate_content(prompt)
        ai_response = response.text

        # 4. AI 응답 DB 저장
        if request.user_id:
            assistant_msg = models.ChatMessage(user_id=request.user_id, role="assistant", content=ai_response)
            db.add(assistant_msg)
            db.commit()
        
        return {"response": ai_response}
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {"response": "죄송합니다. 메시지를 처리하는 중에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}

@app.get("/api/chatbot/history/{user_id}", response_model=List[schemas.ChatMessage])
def get_chatbot_history(user_id: int, db: Session = Depends(get_db)):
    """과거 대화 내역 조회"""
    messages = db.query(models.ChatMessage).filter(models.ChatMessage.user_id == user_id).order_by(models.ChatMessage.created_at.asc()).all()
    return messages

if __name__ == "__main__":

    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
