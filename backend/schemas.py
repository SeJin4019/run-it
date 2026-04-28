from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: str
    name: str
    region: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: int
    friends: List[int] = []

    class Config:
        from_attributes = True

# Course Schemas
class CourseBase(BaseModel):
    name: str
    location: str
    distance: float
    elevation: int
    difficulty: str
    parking: str
    description: Optional[str] = None
    image: Optional[str] = None
    path: List[List[float]]

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    author_id: int
    author_name: Optional[str] = None

    class Config:
        from_attributes = True

# Record Schemas
class RecordBase(BaseModel):
    distance: float
    time: str
    pace: str
    calories: int

class RecordCreate(RecordBase):
    pass

class Record(RecordBase):
    id: int
    date: datetime
    user_id: int

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
