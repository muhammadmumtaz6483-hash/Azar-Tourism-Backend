from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password: Mapped[str]
    fullname: Mapped[str]
    picture: Mapped[str | None]
    role: Mapped[str] 
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
