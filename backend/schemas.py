from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: str
    name: str
    region: Optional[str] = None
    last_seen: Optional[datetime] = None
    profile_image: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ProfileImageUpdate(BaseModel):
    profile_image: str

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
    comments: Optional[List[dict]] = []
    liked_users: Optional[List[int]] = []

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
    cadence: Optional[int] = 0
    splits: Optional[List[dict]] = []
    path: Optional[List[List[float]]] = []
    shoe_id: Optional[int] = None

class RecordCreate(RecordBase):
    pass

class Record(RecordBase):
    id: int
    date: datetime
    user_id: int

    class Config:
        from_attributes = True

# Shoe Schemas
class ShoeBase(BaseModel):
    name: str
    brand: str
    initial_km: float = 0.0
    is_active: bool = True

class ShoeCreate(ShoeBase):
    pass

class Shoe(ShoeBase):
    id: int
    total_km: float
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Live Location Schemas
class LiveLocationUpdate(BaseModel):
    user_id: int
    latitude: float
    longitude: float
    distance: Optional[float] = 0.0
    pace: Optional[str] = "0'00\""
    time: Optional[str] = "00:00:00"
    path: List[List[float]]
    is_active: bool

# Crew Schemas
class CrewMember(BaseModel):
    user_id: int
    name: str
    profile_image: Optional[str] = None
    status: Optional[str] = "accepted"
    distance: float = 0.0
    joined_at: datetime

    class Config:
        from_attributes = True

class CrewBase(BaseModel):
    name: str
    description: str
    image: Optional[str] = None

class CrewCreate(CrewBase):
    pass

class Crew(CrewBase):
    id: int
    leader_id: Optional[int] = None
    total_distance: float = 0.0
    created_at: datetime
    member_count: int = 0
    members: List[CrewMember] = []
    pending_members: List[CrewMember] = []

    class Config:
        from_attributes = True
