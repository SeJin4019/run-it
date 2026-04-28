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

    author = relationship("User", back_populates="courses")

class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    distance = Column(Float)
    time = Column(String) # "00:00:00" 형식
    pace = Column(String) # "0'00\"" 형식
    calories = Column(Integer)
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
