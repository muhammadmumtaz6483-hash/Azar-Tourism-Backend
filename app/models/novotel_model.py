from sqlalchemy import Column, Integer, String, Date, Numeric, Text, TIMESTAMP, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    reference_no = Column(String(100), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    guest_name = Column(String(150), nullable=False)
    hotel = Column(String(200), nullable=False)
    vd = Column(String(50))
    v_no = Column(String(50))
    room_no = Column(String(20))
    pax_adult = Column(Integer, default=1)
    pax_child = Column(Integer, default=0)
    rate_plan = Column(String(100))
    arrival_date = Column(Date, nullable=False)
    departure_date = Column(Date, nullable=False)
    confirmation = Column(String(100))
    passport_no = Column(String(100))
    voucher_no = Column(String(100))
    user_id = Column(String(100))
    nights = Column(Integer, nullable=False)
    actual_rate = Column(Numeric(14, 3), default=0)
    exchange_rate = Column(Numeric(10, 3), default=1)
    selling_rate = Column(Numeric(14, 3), nullable=False)
    new_room_rate = Column(Numeric(14, 3), default=0)
    vat1_10 = Column(Numeric(14, 3), default=0)
    vat7 = Column(Numeric(14, 3), default=0)
    vat20 = Column(Numeric(14, 3), default=0)
    vat5 = Column(Numeric(14, 3), default=0)
    new_vat1_10 = Column(Numeric(14, 3), default=0)
    new_vat7 = Column(Numeric(14, 3), default=0)
    new_vat20 = Column(Numeric(14, 3), default=0)
    new_vat5 = Column(Numeric(14, 3), default=0)
    city_tax_rows = Column(Integer, default=0)
    city_tax_amount = Column(Numeric(10, 3), default=0)
    stamp_tax_rows = Column(Integer, default=0)
    stamp_tax_amount = Column(Numeric(10, 3), default=0)
    sub_total = Column(Numeric(14, 3), nullable=False)
    vat_total = Column(Numeric(14, 3), default=0)
    stamp_tax_total = Column(Numeric(10, 3), default=0)
    city_tax_total = Column(Numeric(10, 3), default=0)
    grand_total = Column(Numeric(14, 3), nullable=False)
    status = Column(String(50), default="Ready")
    batch_no = Column(String(100))
    note = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    

    accommodation_details = relationship("AccommodationDetail", back_populates="invoice", cascade="all, delete-orphan")
    city_tax_details = relationship("CityTaxDetail", back_populates="invoice", cascade="all, delete-orphan")
    stamp_tax_details = relationship("StampTaxDetail", back_populates="invoice", cascade="all, delete-orphan")
    other_services = relationship("OtherService", back_populates="invoice", cascade="all, delete-orphan")

class AccommodationDetail(Base):
    __tablename__ = "accommodation_details"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    day = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(200), nullable=False)
    rate = Column(Numeric(14, 3), nullable=False)
    

    invoice = relationship("Invoice", back_populates="accommodation_details")

class CityTaxDetail(Base):
    __tablename__ = "city_tax_details"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    day = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(10, 3), nullable=False)
    

    invoice = relationship("Invoice", back_populates="city_tax_details")

class StampTaxDetail(Base):
    __tablename__ = "stamp_tax_details"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    day = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(10, 3), nullable=False)
    

    invoice = relationship("Invoice", back_populates="stamp_tax_details")

class OtherService(Base):
    __tablename__ = "other_services"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200))
    date = Column(String(50))
    amount = Column(String(50))
    text_field1 = Column(String(200))
    text_field2 = Column(String(200))
    

    invoice = relationship("Invoice", back_populates="other_services")