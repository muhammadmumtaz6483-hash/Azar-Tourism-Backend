from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from core.database import Base   # your declarative base
class HotelsInfo(Base):
    __tablename__ = "hotel_info"

    id = Column(Integer, primary_key=True, index=True)

    hotel_name = Column(String(100), nullable=False)

    currency = Column(String(3), nullable=False)

    country = Column(String(100), nullable=True)

    form_fields = Column(JSONB, nullable=False)

    accommodation_details = Column(JSONB, nullable=True)

    city_tax = Column(JSONB, nullable=True)

    stamp_tax = Column(JSONB, nullable=True)

    other_services = Column(JSONB, nullable=True)

    final_calculations = Column(JSONB, nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
