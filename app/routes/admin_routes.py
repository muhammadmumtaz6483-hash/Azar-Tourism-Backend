from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.user import User, Page
from models.user import UserPage
from passlib.context import CryptContext
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
from schemas.admin_schema import (
    PageCreateSchema, PageResponseSchema,
    UserPageAssignSchema, UserPageAssignResponseSchema,
    LoginSchema, LoginResponseSchema, PageAccessSchema
)

router = APIRouter(
    prefix="/api",
    tags=["RBAC"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/pages", response_model=PageResponseSchema)
async def create_page(
    payload: PageCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        page = Page(**payload.dict())
        db.add(page)
        await db.commit()
        await db.refresh(page)

        return PageResponseSchema(
            message="Page created successfully",
            page_id=page.id
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign-page", response_model=UserPageAssignResponseSchema)
async def assign_page_to_user(
    payload: UserPageAssignSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_page = UserPage(**payload.dict())
        db.add(user_page)
        await db.commit()
        await db.refresh(user_page)

        return UserPageAssignResponseSchema(
            id=user_page.id,
            message="Page assigned to user successfully"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login(
    data: LoginSchema,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # 🔹 1. User fetch
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 🔹 2. Tokens
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
        secure=False  # ⚠️ production mein True
    )

    # 🔹 3. RBAC (SAFE + OPTIONAL)
    pages = []

    try:
        from models.user import Page
        from models.user import UserPage

        stmt = (
            select(Page, UserPage)
            .join(UserPage, UserPage.page_id == Page.id)
            .where(UserPage.user_id == user.id)
        )

        result = await db.execute(stmt)
        records = result.all()

        for page, up in records:
            pages.append({
                "page_name": page.name,
                "route": page.route,
                "permissions": {
                    "view": up.can_view,
                    "create": up.can_create,
                    "update": up.can_update,
                    "delete": up.can_delete
                }
            })

    except Exception as e:
        # ❗ RBAC fail ho jaye to bhi login fail nahi hoga
        print("RBAC ERROR:", e)

    # 🔹 4. Final Response
    return {
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "fullname": user.fullname,
            "picture": user.picture,
            "role": user.role
        },
        "pages": pages   # frontend sidebar / permissions
    }

