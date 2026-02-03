from pydantic import BaseModel, Field
from typing import Optional, List

# ---------------- Page Schemas ----------------
class PageCreateSchema(BaseModel):
    name: str
    route: str
    can_view: Optional[bool] = False
    can_create: Optional[bool] = False
    can_update: Optional[bool] = False
    can_delete: Optional[bool] = False

class PageResponseSchema(BaseModel):
    page_id: int
    message: str

# ---------------- User Page Assignment Schemas ----------------
class UserPageAssignSchema(BaseModel):
    user_id: int
    page_id: int
    can_view: Optional[bool] = False
    can_create: Optional[bool] = False
    can_update: Optional[bool] = False
    can_delete: Optional[bool] = False

class UserPageAssignResponseSchema(BaseModel):
    id: int
    message: str

# ---------------- Login Schemas ----------------
class LoginSchema(BaseModel):
    email: str
    password: str

class PageAccessSchema(BaseModel):
    page_name: str
    route: str
    permissions: dict

class LoginResponseSchema(BaseModel):
    message: str
    user: dict
    pages: List[PageAccessSchema]
