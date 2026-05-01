from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String)
    region = Column(String, nullable=True)
    friends = Column(JSON, default=[]) # 친구 ID 리스트 저장
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    profile_image = Column(String, nullable=True)

    courses = relationship("Course", back_populates="author")
    records = relationship("Record", back_populates="user")
    shoes = relationship("Shoe", back_populates="user")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)
    distance = Column(Float)
    elevation = Column(Integer)
    difficulty = Column(String)
    parking = Column(String)
    description = Column(String)
    image = Column(String)
    path = Column(JSON) # [[lat, lng], ...] 형태
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    comments = Column(JSON, default=list)
    liked_users = Column(JSON, default=list)

    author = relationship("User", back_populates="courses")

class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    distance = Column(Float)
    time = Column(String) # "00:00:00" 형식
    pace = Column(String) # "0'00\"" 형식
    calories = Column(Integer)
    cadence = Column(Integer, default=0)
    splits = Column(JSON, default=list) # [{km: 1, time: "05:30", pace: "5'30\""}, ...]
    path = Column(JSON, default=list) # [[lat, lng], ...]
    date = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    shoe_id = Column(Integer, ForeignKey("shoes.id"), nullable=True)

    user = relationship("User", back_populates="records")

class Shoe(Base):
    __tablename__ = "shoes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    brand = Column(String)
    initial_km = Column(Float, default=0.0)
    total_km = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="shoes")

class LiveLocation(Base):
    __tablename__ = "live_locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    latitude = Column(Float)
    longitude = Column(Float)
    distance = Column(Float, default=0.0)
    pace = Column(String, default="0'00\"")
    time = Column(String, default="00:00:00")
    path = Column(JSON, default=[]) # 실시간 이동 경로 [[lat, lng], ...]
    is_active = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User")

class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending") # pending, accepted, declined
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])

class Crew(Base):
    __tablename__ = "crews"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    members = relationship("CrewMember", back_populates="crew", cascade="all, delete-orphan")

class CrewMember(Base):
    __tablename__ = "crew_members"
    id = Column(Integer, primary_key=True, index=True)
    crew_id = Column(Integer, ForeignKey("crews.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    crew = relationship("Crew", back_populates="members")
    user = relationship("User")
