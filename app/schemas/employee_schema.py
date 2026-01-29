from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str
    fullname: str
    picture: Optional[str] = None


class EmployeeUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    fullname: Optional[str] = None
    picture: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    email: EmailStr
    fullname: str
    picture: Optional[str]
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
