from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal

class AccommodationDetailSchema(BaseModel):
    day: int
    date: date
    description: str
    rate: float
    
    class Config:
        from_attributes = True

class CityTaxDetailSchema(BaseModel):
    day: int
    date: date
    description: str
    amount: float
    
    class Config:
        from_attributes = True

class StampTaxDetailSchema(BaseModel):
    day: int
    date: date
    description: str
    amount: float
    
    class Config:
        from_attributes = True

class OtherServiceSchema(BaseModel):
    id: Optional[int] = None
    name: str = ""
    date: str = ""
    amount: str = ""
    textField1: str = ""
    textField2: str = ""
    
    class Config:
        from_attributes = True


class InvoiceCreateSchema(BaseModel):
    referenceNo: str = Field(..., min_length=1, max_length=100)
    invoiceDate: date
    guestName: str = Field(..., min_length=1, max_length=150)
    hotel: str = Field(..., min_length=1, max_length=200)
    vd: Optional[str] = Field(None, max_length=50)
    vNo: Optional[str] = Field(None, max_length=50)
    roomNo: Optional[str] = Field(None, max_length=20)
    paxAdult: int = Field(1, ge=0)
    paxChild: int = Field(0, ge=0)
    ratePlan: Optional[str] = Field(None, max_length=100)
    arrivalDate: date
    departureDate: date
    confirmation: Optional[str] = Field(None, max_length=100)
    passportNo: Optional[str] = Field("", max_length=100)
    voucherNo: Optional[str] = Field(None, max_length=100)
    userId: Optional[str] = Field(None, max_length=100)
    nights: int = Field(..., ge=0)
    actualRate: float = Field(0, ge=0)
    exchangeRate: float = Field(1.0, ge=0)
    sellingRate: float = Field(..., ge=0)
    newRoomRate: float = Field(0, ge=0)
    vat1_10: float = Field(0, ge=0)
    vat7: float = Field(0, ge=0)
    vat20: float = Field(0, ge=0)
    vat5: float = Field(0, ge=0)
    newVat1_10: float = Field(0, ge=0)
    newVat7: float = Field(0, ge=0)
    newVat20: float = Field(0, ge=0)
    newVat5: float = Field(0, ge=0)
    cityTaxRows: int = Field(0, ge=0)
    cityTaxAmount: float = Field(0, ge=0)
    stampTaxRows: int = Field(0, ge=0)
    stampTaxAmount: float = Field(0, ge=0)
    subTotal: float = Field(..., ge=0)
    vatTotal: float = Field(0, ge=0)
    stampTaxTotal: float = Field(0, ge=0)
    cityTaxTotal: float = Field(0, ge=0)
    grandTotal: float = Field(..., ge=0)
    accommodationDetails: List[AccommodationDetailSchema] = []
    cityTaxDetails: List[CityTaxDetailSchema] = []
    stampTaxDetails: List[StampTaxDetailSchema] = []
    otherServices: List[OtherServiceSchema] = []
    status: str = Field("Ready", max_length=50)
    batchNo: Optional[str] = Field(None, max_length=100)
    note: Optional[str] = None
    
    @validator('invoiceDate', 'arrivalDate', 'departureDate', pre=True)
    def parse_dates(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                return v
        return v
    
    class Config:
        from_attributes = True

class InvoiceUpdateSchema(BaseModel):
    referenceNo: Optional[str] = Field(None, min_length=1, max_length=100)
    invoiceDate: Optional[date] = None
    guestName: Optional[str] = Field(None, min_length=1, max_length=150)
    hotel: Optional[str] = Field(None, min_length=1, max_length=200)
    vd: Optional[str] = Field(None, max_length=50)
    vNo: Optional[str] = Field(None, max_length=50)
    roomNo: Optional[str] = Field(None, max_length=20)
    paxAdult: Optional[int] = Field(None, ge=0)
    paxChild: Optional[int] = Field(None, ge=0)
    ratePlan: Optional[str] = Field(None, max_length=100)
    arrivalDate: Optional[date] = None
    departureDate: Optional[date] = None
    confirmation: Optional[str] = Field(None, max_length=100)
    passportNo: Optional[str] = Field(None, max_length=100)
    voucherNo: Optional[str] = Field(None, max_length=100)
    userId: Optional[str] = Field(None, max_length=100)
    nights: Optional[int] = Field(None, ge=0)
    actualRate: Optional[float] = Field(None, ge=0)
    exchangeRate: Optional[float] = Field(None, ge=0)
    sellingRate: Optional[float] = Field(None, ge=0)
    newRoomRate: Optional[float] = Field(None, ge=0)
    vat1_10: Optional[float] = Field(None, ge=0)
    vat7: Optional[float] = Field(None, ge=0)
    vat20: Optional[float] = Field(None, ge=0)
    vat5: Optional[float] = Field(None, ge=0)
    newVat1_10: Optional[float] = Field(None, ge=0)
    newVat7: Optional[float] = Field(None, ge=0)
    newVat20: Optional[float] = Field(None, ge=0)
    newVat5: Optional[float] = Field(None, ge=0)
    cityTaxRows: Optional[int] = Field(None, ge=0)
    cityTaxAmount: Optional[float] = Field(None, ge=0)
    stampTaxRows: Optional[int] = Field(None, ge=0)
    stampTaxAmount: Optional[float] = Field(None, ge=0)
    subTotal: Optional[float] = Field(None, ge=0)
    vatTotal: Optional[float] = Field(None, ge=0)
    stampTaxTotal: Optional[float] = Field(None, ge=0)
    cityTaxTotal: Optional[float] = Field(None, ge=0)
    grandTotal: Optional[float] = Field(None, ge=0)
    accommodationDetails: Optional[List[AccommodationDetailSchema]] = None
    cityTaxDetails: Optional[List[CityTaxDetailSchema]] = None
    stampTaxDetails: Optional[List[StampTaxDetailSchema]] = None
    otherServices: Optional[List[OtherServiceSchema]] = None
    status: Optional[str] = Field(None, max_length=50)
    batchNo: Optional[str] = Field(None, max_length=100)
    note: Optional[str] = None

    @validator('invoiceDate', 'arrivalDate', 'departureDate', pre=True)
    def parse_dates(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                return v
        return v

    class Config:
        from_attributes = True

class InvoiceResponseSchema(BaseModel):
    id: int
    referenceNo: str
    invoiceDate: date
    guestName: str
    hotel: str
    roomNo: Optional[str]
    arrivalDate: date
    departureDate: date
    nights: int
    subTotal: float
    grandTotal: float
    status: str
    createdAt: datetime
    
    class Config:
        from_attributes = True

class InvoiceDetailResponseSchema(InvoiceResponseSchema):
    paxAdult: int
    paxChild: int
    sellingRate: float
    vatTotal: float
    cityTaxTotal: float
    stampTaxTotal: float
    batchNo: Optional[str]
    note: Optional[str]
    accommodationDetails: List[Dict]
    cityTaxDetails: List[Dict]
    stampTaxDetails: List[Dict]
    otherServices: List[Dict]
    
    class Config:
        from_attributes = True

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class InvoiceListResponse(BaseModel):
    success: bool
    count: int
    data: List[Dict]