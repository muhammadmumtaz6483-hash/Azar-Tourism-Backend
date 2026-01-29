from pydantic import BaseModel, EmailStr

class SignupSchema(BaseModel):
    email: EmailStr
    password: str
    fullname: str
    picture: str | None = None

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
