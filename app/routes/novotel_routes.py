from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import selectinload
from typing import Dict, Any
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from fastapi.responses import Response
from pydantic import BaseModel
from PIL import Image
from io import BytesIO
import os
import requests
from fastapi import Request
from sqlalchemy import delete, select 


import logging
from schemas.novotel_schema import InvoiceCreateSchema,APIResponse,InvoiceUpdateSchema
from sqlalchemy.exc import IntegrityError

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    font_name = 'Arial'
except:
    font_name = 'Helvetica'  

from core.database import get_db, engine
from models.novotel_model import Invoice, AccommodationDetail, CityTaxDetail, StampTaxDetail, OtherService, Base

logger = logging.getLogger(__name__)

# Create router
n_router = APIRouter(prefix="/api", tags=["New Routes"])

FIELD_MAPPING = {
    # Main invoice fields
    "referenceNo": "reference_no",
    "invoiceDate": "invoice_date",
    "guestName": "guest_name",
    "vNo": "v_no",
    "roomNo": "room_no",
    "paxAdult": "pax_adult",
    "paxChild": "pax_child",
    "ratePlan": "rate_plan",
    "arrivalDate": "arrival_date",
    "departureDate": "departure_date",
    "passportNo": "passport_no",
    "voucherNo": "voucher_no",
    "userId": "user_id",
    "actualRate": "actual_rate",
    "exchangeRate": "exchange_rate",
    "sellingRate": "selling_rate",
    "newRoomRate": "new_room_rate",
    "vat1_10": "vat1_10",
    "newVat1_10": "new_vat1_10",
    "vat7": "vat7",
    "newVat7": "new_vat7",
    "vat20": "vat20",
    "newVat20": "new_vat20",
    "vat5": "vat5",
    "newVat5": "new_vat5",
    "cityTaxRows": "city_tax_rows",
    "cityTaxAmount": "city_tax_amount",
    "stampTaxRows": "stamp_tax_rows",
    "stampTaxAmount": "stamp_tax_amount",
    "subTotal": "sub_total",
    "vatTotal": "vat_total",
    "stampTaxTotal": "stamp_tax_total",
    "cityTaxTotal": "city_tax_total",
    "grandTotal": "grand_total",
    "batchNo": "batch_no",
    
    # Relationship fields (keep as is)
    "accommodationDetails": "accommodation_details",
    "cityTaxDetails": "city_tax_details",
    "stampTaxDetails": "stamp_tax_details",
    "otherServices": "other_services"
}

async def get_complete_invoice_records(db: AsyncSession, invoice_id: int):
    # Main Invoice
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise ValueError("Invoice not found")

    # Accommodation Details
    acc = await db.execute(
        select(AccommodationDetail).where(AccommodationDetail.invoice_id == invoice_id)
    )
    accommodation_details = acc.scalars().all()

    # City Tax Details
    city = await db.execute(
        select(CityTaxDetail).where(CityTaxDetail.invoice_id == invoice_id)
    )
    city_tax_details = city.scalars().all()

    # Stamp Tax Details
    stamp = await db.execute(
        select(StampTaxDetail).where(StampTaxDetail.invoice_id == invoice_id)
    )
    stamp_tax_details = stamp.scalars().all()

    # ✅ Other Services (Fixed)
    services = await db.execute(
        select(OtherService).where(OtherService.invoice_id == invoice_id)
    )
    other_services = services.scalars().all()

    return {
        "invoice": invoice,
        "accommodation_details": accommodation_details,
        "city_tax_details": city_tax_details,
        "stamp_tax_details": stamp_tax_details,
        "other_services": other_services
    }


def handle_error(error: Exception, default_message: str = "Internal server error"):
    """Handle errors and return appropriate HTTP response"""
    logger.error(f"Error occurred: {str(error)}", exc_info=True)
    
    if isinstance(error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    elif isinstance(error, RuntimeError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error))
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=default_message
        )

# ==================== DATABASE INITIALIZATION ENDPOINT ====================
@n_router.post("/init-db")
async def initialize_database():
    """
    Initialize database and create all tables automatically
    """
    try:
        logger.info("Initializing database and creating tables...")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully!")
        
        return {
            "success": True,
            "message": "Database tables created successfully!",
            "data": {
                "tables_created": [
                    "invoices",
                    "accommodation_details", 
                    "city_tax_details",
                    "stamp_tax_details",
                    "other_services"
                ],
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize database: {str(e)}"
        )


# ==================== CHECK DATABASE STATUS ====================
@n_router.get("/db-status")
async def check_database_status():
    """
    Check database connection and table status
    """
    try:
        
        async with engine.connect() as conn:
            # Check connection
            await conn.execute(select(1))
            
            # Check tables using raw SQL query
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            
            required_tables = [
                'invoices',
                'accommodation_details',
                'city_tax_details', 
                'stamp_tax_details',
                'other_services'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            return {
                "success": True,
                "message": "Database connection successful",
                "data": {
                    "connected": True,
                    "tables_found": tables,
                    "required_tables": required_tables,
                    "missing_tables": missing_tables,
                    "all_tables_exist": len(missing_tables) == 0,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return {
            "success": False,
            "message": "Database connection failed",
            "error": str(e),
            "data": {
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
        }


# ==================== ENDPOINT 1: Get All Records From All Tables ====================
@n_router.get("/records/all")
async def get_all_records_from_all_tables(db: AsyncSession = Depends(get_db)):
    """
    Get ALL records from ALL 5 tables - NO input parameters, NO pagination, NO filters
    """
    try:
        logger.info("Getting all records from all tables...")
        
        # Get ALL invoices with ALL related data
        query = (
            select(Invoice)
            .options(
                selectinload(Invoice.accommodation_details),
                selectinload(Invoice.city_tax_details),
                selectinload(Invoice.stamp_tax_details),
                selectinload(Invoice.other_services)
            )
            .order_by(Invoice.created_at.desc())
        )
        
        result = await db.execute(query)
        invoices = result.scalars().all()
        
        # Format all data
        complete_records = []
        for invoice in invoices:
            # Format invoice
            invoice_dict = {}
            for column in invoice.__table__.columns:
                value = getattr(invoice, column.name)
                
                # Handle dates
                if hasattr(value, 'isoformat'):
                    invoice_dict[column.name] = value.isoformat()
                # Handle numeric fields
                elif column.name in ['actual_rate', 'exchange_rate', 'selling_rate', 'new_room_rate',
                                   'vat1_10', 'vat7', 'vat20', 'vat5', 'new_vat1_10', 'new_vat7',
                                   'new_vat20', 'new_vat5', 'city_tax_amount', 'stamp_tax_amount',
                                   'sub_total', 'vat_total', 'stamp_tax_total', 'city_tax_total',
                                   'grand_total'] and value is not None:
                    invoice_dict[column.name] = float(value)
                else:
                    invoice_dict[column.name] = value
            
            # Format accommodation details
            accommodation_details = []
            for detail in sorted(invoice.accommodation_details, key=lambda x: x.day or 0):
                accommodation_details.append({
                    "id": detail.id,
                    "invoice_id": detail.invoice_id,
                    "day": detail.day,
                    "date": detail.date.isoformat() if detail.date else None,
                    "description": detail.description,
                    "rate": float(detail.rate) if detail.rate else None
                })
            
            # Format city tax details
            city_tax_details = []
            for detail in sorted(invoice.city_tax_details, key=lambda x: x.day or 0):
                city_tax_details.append({
                    "id": detail.id,
                    "invoice_id": detail.invoice_id,
                    "day": detail.day,
                    "date": detail.date.isoformat() if detail.date else None,
                    "description": detail.description,
                    "amount": float(detail.amount) if detail.amount else None
                })
            
            # Format stamp tax details
            stamp_tax_details = []
            for detail in sorted(invoice.stamp_tax_details, key=lambda x: x.day or 0):
                stamp_tax_details.append({
                    "id": detail.id,
                    "invoice_id": detail.invoice_id,
                    "day": detail.day,
                    "date": detail.date.isoformat() if detail.date else None,
                    "description": detail.description,
                    "amount": float(detail.amount) if detail.amount else None
                })
            
            # Format other services
            other_services = []
            for service in invoice.other_services:
                other_services.append({
                    "id": service.id,
                    "invoice_id": service.invoice_id,
                    "name": service.name,
                    "date": service.date,
                    "amount": service.amount,
                    "text_field1": service.text_field1,
                    "text_field2": service.text_field2
                })
            
            complete_records.append({
                "invoice": invoice_dict,
                "accommodation_details": accommodation_details,
                "city_tax_details": city_tax_details,
                "stamp_tax_details": stamp_tax_details,
                "other_services": other_services
            })
        
        # Get total counts
        invoice_count = len(invoices)
        
        acc_result = await db.execute(select(AccommodationDetail))
        accommodation_count = len(acc_result.scalars().all())
        
        city_result = await db.execute(select(CityTaxDetail))
        city_tax_count = len(city_result.scalars().all())
        
        stamp_result = await db.execute(select(StampTaxDetail))
        stamp_tax_count = len(stamp_result.scalars().all())
        
        other_result = await db.execute(select(OtherService))
        other_services_count = len(other_result.scalars().all())
        
        total_records = invoice_count + accommodation_count + city_tax_count + stamp_tax_count + other_services_count
        
        return {
            "success": True,
            "message": f"Successfully retrieved {total_records} records from all tables",
            "data": {
                "total_records": total_records,
                "table_counts": {
                    "invoices": invoice_count,
                    "accommodation_details": accommodation_count,
                    "city_tax_details": city_tax_count,
                    "stamp_tax_details": stamp_tax_count,
                    "other_services": other_services_count
                },
                "records": complete_records
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting all records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get all records: {str(e)}"
        )


# ==================== ENDPOINT 2: Get Complete Invoice ====================
@n_router.get("/invoices/{invoice_id}/complete")
async def get_complete_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get complete invoice with all related records
    """
    try:
        query = (
            select(Invoice)
            .where(Invoice.id == invoice_id)
            .options(
                selectinload(Invoice.accommodation_details),
                selectinload(Invoice.city_tax_details),
                selectinload(Invoice.stamp_tax_details),
                selectinload(Invoice.other_services)
            )
        )
        
        result = await db.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Format the response
        invoice_data = {}
        for column in invoice.__table__.columns:
            value = getattr(invoice, column.name)
            if hasattr(value, 'isoformat'):
                invoice_data[column.name] = value.isoformat()
            elif column.name in ['grand_total', 'sub_total', 'vat_total'] and value is not None:
                invoice_data[column.name] = float(value)
            else:
                invoice_data[column.name] = value
        
        return {
            "success": True,
            "message": "Complete invoice retrieved",
            "data": {
                "invoice": invoice_data,
                "accommodation_details": [
                    {
                        "id": d.id,
                        "day": d.day,
                        "date": d.date.isoformat() if d.date else None,
                        "description": d.description,
                        "rate": float(d.rate) if d.rate else None
                    }
                    for d in sorted(invoice.accommodation_details, key=lambda x: x.day or 0)
                ],
                "city_tax_details": [
                    {
                        "id": d.id,
                        "day": d.day,
                        "date": d.date.isoformat() if d.date else None,
                        "description": d.description,
                        "amount": float(d.amount) if d.amount else None
                    }
                    for d in sorted(invoice.city_tax_details, key=lambda x: x.day or 0)
                ],
                "stamp_tax_details": [
                    {
                        "id": d.id,
                        "day": d.day,
                        "date": d.date.isoformat() if d.date else None,
                        "description": d.description,
                        "amount": float(d.amount) if d.amount else None
                    }
                    for d in sorted(invoice.stamp_tax_details, key=lambda x: x.day or 0)
                ],
                "other_services": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "date": s.date,
                        "amount": s.amount,
                        "text_field1": s.text_field1,
                        "text_field2": s.text_field2
                    }
                    for s in invoice.other_services
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINT 3: Update Complete Invoice ====================
@n_router.put("/updateinvoices/{invoice_id}")
async def update_invoice_endpoint(
    invoice_id: int,
    invoice_data: InvoiceUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        # ================= FETCH EXISTING INVOICE WITH RELATIONSHIPS =================
        from sqlalchemy.orm import selectinload
        
        # Load invoice with relationships
        from sqlalchemy import select
        query = select(Invoice).where(Invoice.id == invoice_id).options(
            selectinload(Invoice.accommodation_details),
            selectinload(Invoice.city_tax_details),
            selectinload(Invoice.stamp_tax_details),
            selectinload(Invoice.other_services)
        )
        result = await db.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Get update data (exclude relationships)
        update_data = invoice_data.dict(exclude_unset=True)
        
        # ================= UPDATE MAIN FIELDS =================
        for field, value in update_data.items():
            # Skip relationship fields for now (handle separately)
            if field in ("accommodationDetails", "cityTaxDetails", "stampTaxDetails", "otherServices"):
                continue
                
            # Get snake_case field name from mapping
            snake_field = FIELD_MAPPING.get(field, field)  # Default to original if not in mapping
            if hasattr(invoice, snake_field):
                setattr(invoice, snake_field, value)

        # ================= UPDATE RELATIONSHIPS =================
        # Use manual DELETE and INSERT for async compatibility
        
        if invoice_data.accommodationDetails is not None:
            # Delete existing accommodation details
            await db.execute(
                delete(AccommodationDetail)
                .where(AccommodationDetail.invoice_id == invoice_id)
            )
            # Add new ones if list is not empty
            if invoice_data.accommodationDetails:
                for row in invoice_data.accommodationDetails:
                    new_detail = AccommodationDetail(
                        invoice_id=invoice_id,
                        day=row.day,
                        date=row.date,
                        description=row.description,
                        rate=row.rate
                    )
                    db.add(new_detail)

        if invoice_data.cityTaxDetails is not None:
            await db.execute(
                delete(CityTaxDetail)
                .where(CityTaxDetail.invoice_id == invoice_id)
            )
            if invoice_data.cityTaxDetails:
                for row in invoice_data.cityTaxDetails:
                    new_detail = CityTaxDetail(
                        invoice_id=invoice_id,
                        day=row.day,
                        date=row.date,
                        description=row.description,
                        amount=row.amount
                    )
                    db.add(new_detail)

        if invoice_data.stampTaxDetails is not None:
            await db.execute(
                delete(StampTaxDetail)
                .where(StampTaxDetail.invoice_id == invoice_id)
            )
            if invoice_data.stampTaxDetails:
                for row in invoice_data.stampTaxDetails:
                    new_detail = StampTaxDetail(
                        invoice_id=invoice_id,
                        day=row.day,
                        date=row.date,
                        description=row.description,
                        amount=row.amount
                    )
                    db.add(new_detail)

        if invoice_data.otherServices is not None:
            await db.execute(
                delete(OtherService)
                .where(OtherService.invoice_id == invoice_id)
            )
            valid_services = [
                row for row in invoice_data.otherServices
                if row.name or row.amount
            ]
            if valid_services:
                for row in valid_services:
                    new_service = OtherService(
                        invoice_id=invoice_id,
                        name=row.name,
                        date=row.date,
                        amount=row.amount,
                        text_field1=row.textField1,
                        text_field2=row.textField2
                    )
                    db.add(new_service)

        # Commit all changes
        await db.commit()
        
        # Refresh the invoice to get updated data
        await db.refresh(invoice)

        return {
            "success": True,
            "message": "Invoice updated successfully",
            "data": {
                "id": invoice.id,
                "reference_no": invoice.reference_no,
                "status": invoice.status,
                "grand_total": float(invoice.grand_total)
            }
        }

    except IntegrityError as e:
        await db.rollback()
        if "reference_no" in str(e.orig).lower():
            raise HTTPException(
                status_code=400,
                detail="Invoice with this reference number already exists"
            )
        # Log the full error for debugging
        print(f"IntegrityError: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Database integrity error: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        # Log the full error traceback for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Error updating invoice {invoice_id}: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update invoice: {str(e)}"
        )

# ==================== ENDPOINT 4: Search Invoices by Name ====================
@n_router.get("/invoices/search/name")
async def search_invoices_by_name(
    search_term: str = Query(..., description="Search term"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Search invoices by name/hotel/reference
    """
    try:
        query = (
            select(Invoice)
            .where(
                or_(
                    Invoice.guest_name.ilike(f"%{search_term}%"),
                    Invoice.hotel.ilike(f"%{search_term}%"),
                    Invoice.reference_no.ilike(f"%{search_term}%")
                )
            )
            .order_by(Invoice.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        invoices = result.scalars().all()
        
        formatted = []
        for invoice in invoices:
            formatted.append({
                "id": invoice.id,
                "reference_no": invoice.reference_no,
                "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "guest_name": invoice.guest_name,
                "hotel": invoice.hotel,
                "room_no": invoice.room_no,
                "grand_total": float(invoice.grand_total) if invoice.grand_total else 0,
                "status": invoice.status
            })
        
        return {
            "success": True,
            "message": f"Found {len(formatted)} invoices",
            "data": formatted
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 5: Create Invoice ====================
@n_router.post("/invoices")
async def create_invoice_endpoint(
    invoice_data: InvoiceCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        invoice = Invoice(
            reference_no=invoice_data.referenceNo,
            invoice_date=invoice_data.invoiceDate,
            guest_name=invoice_data.guestName,
            hotel=invoice_data.hotel,
            vd=invoice_data.vd,
            v_no=invoice_data.vNo,
            room_no=invoice_data.roomNo,
            pax_adult=invoice_data.paxAdult,
            pax_child=invoice_data.paxChild,
            rate_plan=invoice_data.ratePlan,
            arrival_date=invoice_data.arrivalDate,
            departure_date=invoice_data.departureDate,
            confirmation=invoice_data.confirmation,
            passport_no=invoice_data.passportNo,
            voucher_no=invoice_data.voucherNo,
            user_id=invoice_data.userId,
            nights=invoice_data.nights,
            actual_rate=invoice_data.actualRate,
            exchange_rate=invoice_data.exchangeRate,
            selling_rate=invoice_data.sellingRate,
            new_room_rate=invoice_data.newRoomRate,
            vat1_10=invoice_data.vat1_10,
            vat7=invoice_data.vat7,
            vat20=invoice_data.vat20,
            vat5=invoice_data.vat5,
            new_vat1_10=invoice_data.newVat1_10,
            new_vat7=invoice_data.newVat7,
            new_vat20=invoice_data.newVat20,
            new_vat5=invoice_data.newVat5,
            city_tax_rows=invoice_data.cityTaxRows,
            city_tax_amount=invoice_data.cityTaxAmount,
            stamp_tax_rows=invoice_data.stampTaxRows,
            stamp_tax_amount=invoice_data.stampTaxAmount,
            sub_total=invoice_data.subTotal,
            vat_total=invoice_data.vatTotal,
            stamp_tax_total=invoice_data.stampTaxTotal,
            city_tax_total=invoice_data.cityTaxTotal,
            grand_total=invoice_data.grandTotal,
            status=invoice_data.status,
            batch_no=invoice_data.batchNo,
            note=invoice_data.note
        )

        db.add(invoice)
        await db.flush()   # get invoice.id

        # Accommodation Details
        for acc_detail in invoice_data.accommodationDetails:
            db.add(AccommodationDetail(
                invoice_id=invoice.id,
                day=acc_detail.day,
                date=acc_detail.date,
                description=acc_detail.description,
                rate=acc_detail.rate
            ))

        # City Tax Details
        for city_tax in invoice_data.cityTaxDetails:
            db.add(CityTaxDetail(
                invoice_id=invoice.id,
                day=city_tax.day,
                date=city_tax.date,
                description=city_tax.description,
                amount=city_tax.amount
            ))

        # Stamp Tax Details
        for stamp_tax in invoice_data.stampTaxDetails:
            db.add(StampTaxDetail(
                invoice_id=invoice.id,
                day=stamp_tax.day,
                date=stamp_tax.date,
                description=stamp_tax.description,
                amount=stamp_tax.amount
            ))

        # Other Services
        for service in invoice_data.otherServices:
            if service.name or service.amount:
                db.add(OtherService(
                    invoice_id=invoice.id,
                    name=service.name,
                    date=service.date,
                    amount=service.amount,
                    text_field1=service.textField1,
                    text_field2=service.textField2
                ))

        await db.commit()

        return {
            "success": True,
            "message": "Invoice created successfully",
            "data": {
                "id": invoice.id,
                "reference_no": invoice.reference_no,
                "guest_name": invoice.guest_name,
                "grand_total": float(invoice.grand_total),
                "status": invoice.status
            }
        }

    except IntegrityError as e:
        await db.rollback()
        if "reference_no" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"Invoice with reference number '{invoice_data.referenceNo}' already exists"
            )
        raise HTTPException(status_code=400, detail="Database integrity error")

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")


# ==================== ENDPOINT 6: Get Invoice by ID ====================
@n_router.get("/invoices/{invoice_id}")
async def get_invoice_by_id(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get invoice by ID
    """
    try:
        result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Format response
        invoice_data = {}
        for column in invoice.__table__.columns:
            value = getattr(invoice, column.name)
            if hasattr(value, 'isoformat'):
                invoice_data[column.name] = value.isoformat()
            elif isinstance(value, (int, float)):
                invoice_data[column.name] = float(value)
            else:
                invoice_data[column.name] = value
        
        return {
            "success": True,
            "message": "Invoice retrieved",
            "data": invoice_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 7: Delete Invoice ====================
@n_router.delete("/invoices/{invoice_id}")
async def delete_invoice_endpoint(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete invoice
    """
    try:
        # Check if exists
        result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Delete (cascade will handle related records)
        await db.execute(Invoice.__table__.delete().where(Invoice.id == invoice_id))
        await db.commit()
        
        return {
            "success": True,
            "message": "Invoice deleted",
            "data": None
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 8: PDF Generate ====================
# ==================== ENDPOINT 8: PDF Generate ====================
@n_router.post("/generate-pdf-direct")
async def generate_pdf_direct(data: dict):
    """
    Generate PDF with exact jsPDF positioning using ReportLab
    Compact footer like in the image with stamp at bottom
    """

    invoice_no = str(data.get('invoiceNo', 'invoice'))
    safe_invoice_no = ''.join(c for c in invoice_no if c.isalnum() or c in ('_', '-'))
    
    def optimize_image(image_path_or_url, max_width=800, max_height=600, quality=85):
        """Compress and resize image for PDF"""
        try:
            if isinstance(image_path_or_url, str) and image_path_or_url.startswith('http'):
                response = requests.get(image_path_or_url, timeout=2)
                img = Image.open(BytesIO(response.content))
            else:
                img = Image.open(image_path_or_url)
            
            # Convert to RGB (removes alpha channel if present)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Resize if larger than max dimensions
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save to buffer with compression
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=quality, optimize=True)
            img_buffer.seek(0)
            
            return ImageReader(img_buffer)
        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")
            return None

    def paginate_lines(lines, rows_per_page=30):
        """Split lines into pages with specified rows per page"""
        paginated = []
        total_lines = len(lines)
        
        for i in range(0, total_lines, rows_per_page):
            page_lines = lines[i:i + rows_per_page]
            page_num = len(paginated) + 1
            
            # Check if this is the last page
            is_last_page = (i + rows_per_page >= total_lines)
            
            paginated.append({
                'pageNum': page_num,
                'lines': page_lines,
                'isLastPage': is_last_page,
                'totalPages': (total_lines + rows_per_page - 1) // rows_per_page
            })
        
        return paginated
    
    try:
        logger.info("📄 Starting PDF generation")
        
        # Get invoice data from request
        invoice_data = data.get("invoice")
        if not invoice_data:
            raise HTTPException(400, "Invoice data required")
        
        logger.info(f"📝 Received invoice data")
        
        # Extract invoice number or reference number for filename
        invoice = invoice_data.get("invoice", {})
        invoice_number = invoice.get('invoiceNo', '')
        reference_number = invoice.get('referenceNo', '')
        
        # Use invoice number if available, otherwise use reference number
        if invoice_number:
            file_identifier = invoice_number
        elif reference_number:
            file_identifier = reference_number
        else:
            file_identifier = safe_invoice_no
        
        # Clean the filename for safe use
        safe_filename = ''.join(c for c in str(file_identifier) if c.isalnum() or c in ('_', '-', ' '))
        if not safe_filename.strip():
            safe_filename = "Invoice"
        
        # Create PDF
        pdf_buffer = BytesIO()
        doc = canvas.Canvas(pdf_buffer, pagesize=A4)
        doc.setPageCompression(1) 
        doc.setTitle(f"NOVOTEL - {safe_filename}")
        
        # Constants (matching jsPDF exactly)
        page_width = 210 * mm
        page_height = 297 * mm
        margin_l = 15 * mm
        margin_r = 15 * mm
        stamp_w = 30 * mm
        stamp_h = 15 * mm
        
        # Load images
        logo_img = None
        stamp_img = None
        
        # Try multiple methods to load and optimize logo
        logo_paths = [
            "../app/routes/logo/novotel_logo/novotel_logo.png",
            "./public/novotel_logo.png",
            "../frontend/public/novotel_logo.png",
            "https://azar-front-end.vercel.app/novotel_logo.png"
        ]
        
        for path in logo_paths:
            try:
                if os.path.exists(path) or path.startswith('http'):
                    logo_img = optimize_image(path, max_width=1000, max_height=200, quality=85)
                    if logo_img:
                        logger.info(f"✅ Logo loaded and optimized from: {path}")
                        break
            except:
                continue
        
        if not logo_img:
            logger.warning("⚠️ Logo not found")
        
        # Try multiple methods to load and optimize stamp
        stamp_paths = [
            "../app/routes/logo/novotel_logo/novotel_stemp.png",
            "./public/novotel_stemp.png",
            "../frontend/public/novotel_stemp.png",
            "https://azar-front-end.vercel.app/novotel_stemp.png"
        ]
        
        for path in stamp_paths:
            try:
                if os.path.exists(path) or path.startswith('http'):
                    stamp_img = optimize_image(path, max_width=600, max_height=600, quality=85)
                    if stamp_img:
                        logger.info(f"✅ Stamp loaded and optimized from: {path}")
                        break
            except:
                continue
        
        if not stamp_img:
            logger.warning("⚠️ Stamp not found")
        
        # Get all lines and paginate them with 30 rows per page
        all_lines = invoice.get("lines", [])
        paginated_data = paginate_lines(all_lines, rows_per_page=30)
        
        # If no paginated data from client, create it from all lines
        if not paginated_data and all_lines:
            paginated_data = paginate_lines(all_lines, rows_per_page=30)
        
        # Process each page
        for page_idx, page_data in enumerate(paginated_data):
            if page_idx > 0:
                doc.showPage()
            
            total_pages = page_data.get('totalPages', len(paginated_data))
            y = page_height - 12 * mm  # Start from top
            
            # 1. Logo (centered)
            if logo_img:
                logo_w = 70 * mm
                logo_h = 13 * mm
                logo_x = (page_width - logo_w) / 2
                doc.drawImage(logo_img, logo_x, y - logo_h, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
                y -= logo_h + 15 * mm
            else:
                y -= 20 * mm
            
            # 2. Header Info
            doc.setFont(font_name, 9)
            left_x = margin_l
            right_x = page_width / 2 + 5 * mm
            line_height = 4.2 * mm
            
            # Left Column
            ly = y
            doc.drawString(left_x, ly, f"Name : {invoice.get('guestName', '')}")
            ly -= line_height
            doc.drawString(left_x, ly, f"Person(s) : {invoice.get('persons', '')}")
            ly -= line_height
            doc.drawString(left_x, ly, f"Room No. : {invoice.get('roomNo', '')}")
            ly -= line_height
            doc.drawString(left_x, ly, f"Arrival : {invoice.get('arrival', '')}")
            ly -= line_height
            doc.drawString(left_x, ly, f"Departure : {invoice.get('departure', '')}")
            ly -= line_height
            doc.drawString(left_x, ly, "Novotel Tunis Lac,")
            ly -= line_height
            doc.drawString(left_x, ly, f"The {invoice.get('issueDate', '')}")
            
            # Right Column
            ry = y
            right_max_w = page_width - margin_r - right_x
            
            # Company (with wrapping)
            company_text = f"Company : {invoice.get('companyName', '')}"
            if doc.stringWidth(company_text, font_name, 9) > right_max_w:
                words = company_text.split()
                line = ""
                for word in words:
                    test = line + " " + word if line else word
                    if doc.stringWidth(test, font_name, 9) <= right_max_w:
                        line = test
                    else:
                        if line:
                            doc.drawString(right_x, ry, line)
                            ry -= line_height
                        line = word
                if line:
                    doc.drawString(right_x, ry, line)
                    ry -= line_height
            else:
                doc.drawString(right_x, ry, company_text)
                ry -= line_height
            
            # Address (with wrapping)
            address_text = f"Address : {invoice.get('companyAddress', '')}"
            if doc.stringWidth(address_text, font_name, 9) > right_max_w:
                words = address_text.split()
                line = ""
                for word in words:
                    test = line + " " + word if line else word
                    if doc.stringWidth(test, font_name, 9) <= right_max_w:
                        line = test
                    else:
                        if line:
                            doc.drawString(right_x, ry, line)
                            ry -= line_height
                        line = word
                if line:
                    doc.drawString(right_x, ry, line)
                    ry -= line_height
            else:
                doc.drawString(right_x, ry, address_text)
                ry -= line_height
            
            ry -= 1 * mm
            doc.drawString(right_x, ry, f"Account NO : {invoice.get('accountNo', '')}")
            ry -= line_height
            doc.drawString(right_x, ry, f"VAT No : {invoice.get('vatNo', '')}")
            ry -= line_height
            doc.drawString(right_x, ry, f"Invoice No: {invoice.get('invoiceNo', '')}")
            ry -= line_height
            doc.drawString(right_x, ry, f"Cashier : {invoice.get('cashier', '')}")
            ry -= line_height
            doc.drawString(right_x, ry, f"Pages : {page_data.get('pageNum', 1)} of {total_pages}")
            
            # Move y to the lower of the two columns
            y = min(ly, ry) - 10 * mm
            
            # 3. Table Header
            doc.setFillColorRGB(235/255, 235/255, 235/255)
            doc.rect(margin_l, y - 7 * mm, page_width - margin_l - margin_r, 7 * mm, fill=1, stroke=0)
            doc.setStrokeColorRGB(0, 0, 0)
            doc.setLineWidth(0.3)
            doc.line(margin_l, y, page_width - margin_r, y)
            doc.line(margin_l, y - 7 * mm, page_width - margin_r, y - 7 * mm)

            doc.setFillColorRGB(0, 0, 0)
            doc.setFont(font_name, 9)
            doc.drawString(margin_l + 2 * mm, y - 5 * mm, "Date")
            doc.drawString(margin_l + 30 * mm, y - 5 * mm, "Description")

            # DEBITS
            doc.drawRightString(page_width - margin_r - 35 * mm, y - 2.5 * mm, "Debits")
            doc.setFont(font_name, 9)
            doc.drawRightString(page_width - margin_r - 35 * mm, y - 6.5 * mm, invoice.get('currency', 'TND'))

            # CREDITS
            doc.setFont(font_name, 9)
            doc.drawRightString(page_width - margin_r - 2 * mm, y - 2.5 * mm, "Credits")
            doc.setFont(font_name, 9)
            doc.drawRightString(page_width - margin_r - 2 * mm, y - 6.5 * mm, invoice.get('currency', 'TND'))
                        
            # Move down after the header
            y -= 12 * mm
            
            # 4. Table Rows (Exactly 30 rows per page)
            doc.setFont(font_name, 9)
            row_height = 5 * mm  # Optimal height for 30 rows
            
            # Get lines for this page
            page_lines = page_data.get('lines', [])
            
            # Display exactly 30 rows (or available rows for last page)
            rows_to_display = 30 if not page_data.get('isLastPage', False) else len(page_lines)
            
            for line_idx in range(rows_to_display):
                if line_idx < len(page_lines):
                    line = page_lines[line_idx]
                    doc.drawString(margin_l + 2 * mm, y, line.get('date', ''))
                    doc.drawString(margin_l + 30 * mm, y, line.get('description', ''))
                    
                    debit_val = float(line.get('debit', 0))
                    credit_val = float(line.get('credit', 0))
                    
                    doc.drawRightString(page_width - margin_r - 35 * mm, y, f"{debit_val:.3f}")
                    doc.drawRightString(page_width - margin_r - 2 * mm, y, f"{credit_val:.3f}")
                
                y -= row_height
            
            # 5. Footer (only on last page) - COMPACT LIKE IN IMAGE
            if page_data.get('isLastPage', False):
                # Calculate totals
                total_debit = sum(float(l.get('debit', 0)) for l in all_lines)
                total_credit = sum(float(l.get('credit', 0)) for l in all_lines)
                exchange_rate = float(invoice.get('exchangeRate', 2.85))
                total_usd = total_debit / exchange_rate
                currency = invoice.get('currency', 'TND')
                
                # Calculate tax values based on total
                net_taxable = float(invoice.get('netTaxable', total_debit * 100/109.19))
                fdcst = float(invoice.get('fdsct', net_taxable * 0.01))
                vat7 = float(invoice.get('vat7Total', net_taxable * 0.07))
                vat19 = 0.0
                city_tax = float(invoice.get('cityTaxTotal', 0))
                stamp_tax = float(invoice.get('stampTaxTotal', 0))
                non_revenue = 0.0
                paid_out = 0.0
                total_gross = float(invoice.get('grossTotal', total_debit))
                
                # Start footer immediately after last row
                # Make sure we have enough space for stamp at bottom
                min_y_for_stamp = 30 * mm  # Stamp needs about 30mm space
                
                # If y is too low, adjust it
                if y < min_y_for_stamp:
                    y = min_y_for_stamp + 10 * mm
                
                # Total line
                doc.line(margin_l, y, page_width - margin_r, y)
                y -= 4.2 * mm
                
                # Total row (like in your image - right aligned)
                doc.setFont(font_name, 9)
                doc.drawString(margin_l + 80 * mm, y, "Total")
                doc.drawRightString(page_width - margin_r - 35 * mm, y, f"{total_debit:.3f}")
                doc.drawRightString(page_width - margin_r - 2 * mm, y, f"{total_credit:.3f}")
                
                y -= 2 * mm
                # Balance line (shorter line)
                doc.line(margin_l + 80 * mm, y, page_width - margin_r, y)
                y -= 4.2 * mm
                
                # Balance row
                doc.drawString(margin_l + 80 * mm, y, "Balance")
                balance_text = f"{total_debit:.3f} {currency}"
                doc.drawRightString(page_width - margin_r - 2 * mm, y, balance_text)
                
                # Tax section - COMPACT, TWO COLUMNS (as in your image)
                # Left side: Tax labels and values
                tax_start_y = y - 6 * mm  # Close to balance
                tax_label_x = margin_l
                tax_value_x = margin_l + 60 * mm
                tax_row_height = 4 * mm  # Compact spacing
                
                ty = tax_start_y
                
                # Tax items for left column (from your image)
                left_tax_items = [
                    ("Net Taxable", f"{net_taxable:.3f} {currency}"),
                    ("FDCTST 1 %", f"{fdcst:.3f} {currency}"),
                    ("VAT 7%", f"{vat7:.3f} {currency}"),
                    ("VAT 19%", f"{vat19:.3f} {currency}"),
                    ("City Tax", f"{city_tax:.3f} {currency}"),
                    ("Stamp Tax", f"{stamp_tax:.3f} {currency}"),
                    ("Non Revenue", f"{non_revenue:.3f} {currency}")
                ]
                
                # Draw left tax column
                for label, value in left_tax_items:
                    doc.drawString(tax_label_x, ty, label)
                    doc.drawString(tax_value_x, ty, value)
                    ty -= tax_row_height
                
                # Right side: USD and other items (aligned with last items)
                right_start_y = tax_start_y
                right_label_x = page_width / 2 + 10 * mm
                right_value_x = page_width - margin_r - 40 * mm
                
                # Items for right column (from your image)
                right_items = [
                    ("USD Exch. Rate:", f"{exchange_rate:.2f} {currency}"),
                    ("Paid Out", f"{paid_out:.3f} {currency}"),
                    ("Total in USD:", f"{total_usd:.2f} USD"),
                    ("Total Gross", f"{total_gross:.3f} {currency}")
                ]
                
                ry = right_start_y
                
                for i, (label, value) in enumerate(right_items):
                    # Align with corresponding left items
                    if i == 0:  # USD Exch Rate
                        ry = tax_start_y - 3 * tax_row_height
                    elif i == 1:  # Paid Out
                        ry = tax_start_y - 6 * tax_row_height
                    elif i == 2:  # Total in USD
                        ry = tax_start_y - 7 * tax_row_height
                    elif i == 3:  # Total Gross
                        ry = tax_start_y - 8 * tax_row_height
                    
                    doc.drawString(right_label_x, ry, label)
                    doc.drawString(right_value_x, ry, value)
            
            # 6. Stamp (on EVERY page - bottom right corner, BELOW everything)
            # Stamp should be at very bottom, below all text
            if stamp_img:
                stamp_x = page_width - stamp_w - 5 * mm
                stamp_y = 10 * mm  # 10mm from bottom
                
                # Check if stamp would overlap with text on last page
                if page_data.get('isLastPage', False):
                    # Calculate lowest text position
                    lowest_text = min(y, ty if 'ty' in locals() else y, ry if 'ry' in locals() else y)
                    
                    # If stamp would overlap, move stamp lower or text higher
                    if lowest_text < stamp_y + stamp_h + 5 * mm:
                        # Move stamp a bit lower
                        stamp_y = 5 * mm
                
                doc.drawImage(stamp_img, stamp_x, stamp_y, width=stamp_w, height=stamp_h, preserveAspectRatio=False, mask='auto')
        
        # Save PDF
        doc.save()
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        if len(pdf_bytes) < 1000:
            raise RuntimeError("PDF too small")
        
        # Create proper filename
        pdf_filename = f"NOVOTEL_{safe_filename}.pdf"
        
        logger.info(f"✅ PDF generated: {len(pdf_bytes)} bytes - Filename: {pdf_filename}")
        logger.info(f"📊 Pages: {len(paginated_data)}, Rows per page: 30")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_filename}"',
                "Content-Length": str(len(pdf_bytes)),
                "Cache-Control": "no-cache"
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(500, f"PDF failed: {str(e)}")
