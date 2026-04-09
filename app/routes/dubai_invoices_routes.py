from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from models.dubai_hotel import DubaiHotel
from core.database import get_db


router = APIRouter(
    prefix="/api/dubai-invoices",
    tags=["Dubai Invoices"]
)

@router.get("/")
async def get_all_invoices(
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(
        select(DubaiHotel)
    )
    records = result.scalars().all()

    return {
        "success": True,
        "count": len(records),
        "data": records
    }


@router.get("/{invoice_id}")
async def get_invoice_by_id(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    invoice = await session.get(DubaiHotel, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return {
        "success": True,
        "data": invoice
    }


@router.post("/")
async def create_invoice(
    payload: dict,
    session: AsyncSession = Depends(get_db)
):
    invoice = DubaiHotel(data=payload)

    session.add(invoice)
    await session.commit()
    await session.refresh(invoice)

    return {
        "success": True,
        "message": "Invoice created successfully",
        "data": invoice
    }


@router.put("/{invoice_id}")
async def update_invoice(
    invoice_id: UUID,
    payload: dict,
    session: AsyncSession = Depends(get_db)
):
    invoice = await session.get(DubaiHotel, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.data = payload
    await session.commit()
    await session.refresh(invoice)

    return {
        "success": True,
        "message": "Invoice updated successfully",
        "data": invoice
    }


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    invoice = await session.get(DubaiHotel, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    await session.delete(invoice)
    await session.commit()

    return {
        "success": True,
        "message": "Invoice deleted successfully"
    }
