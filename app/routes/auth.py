from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.user_schema import LoginSchema
from models.user import User
from core.database import get_db
from fastapi import UploadFile, File, Form
import os
from uuid import uuid4
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
from core.confiq import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    ALGORITHM
)
from jose import jwt, JWTError

UPLOAD_DIR = "uploads/profile"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# ✅ SIGNUP
@router.post("/signup")
async def signup(
    email: str = Form(...),
    password: str = Form(...),
    fullname: str = Form(...),
    picture: UploadFile = File(None),
    role: str = Form(...),
    db: AsyncSession = Depends(get_db)
):

    # ✅ Password Validation
    if len(password) < 8 or len(password) > 128:
        raise HTTPException(
            status_code=400,
            detail="Password must be between 8 and 128 characters"
        )

    # ✅ Check existing email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    filename = None

    if picture:
        ext = picture.filename.split(".")[-1]
        filename = f"{uuid4()}.{ext}"

        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(await picture.read())

    user = User(
        email=email,
        password=hash_password(password),
        fullname=fullname,
        picture=filename,
        role=role
    )

    db.add(user)
    await db.commit()

    return {"message": "User created successfully"}


# ✅ LOGIN
@router.post("/login")
async def login(
    data: LoginSchema,
    response: Response,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        {"id": user.id, "role": user.role},
        ACCESS_TOKEN_EXPIRE_MINUTES
    )

    refresh_token = create_refresh_token(
        {"id": user.id},
        REFRESH_TOKEN_EXPIRE_DAYS
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False  # 🔥 CHANGE TO TRUE IN PRODUCTION (HTTPS)
    )

    return {
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "fullname": user.fullname,
            "picture": user.picture,
            "role": user.role
        }
    }


# ✅ REFRESH TOKEN
@router.post("/refresh")
async def refresh(request: Request):

    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = create_access_token(
        {"id": payload["id"]},
        ACCESS_TOKEN_EXPIRE_MINUTES
    )

    return {"access_token": new_access}
