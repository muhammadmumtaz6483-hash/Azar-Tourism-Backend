from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from core.database import get_db

from models.turkey_hotel import TurkeyHotel

router = APIRouter(
    prefix="/api/turkey-invoices",
    tags=["Turkey Invoices"]
)

@router.get("/")
async def get_all_invoices(
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(
        select(TurkeyHotel)
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
    invoice = await session.get(TurkeyHotel, invoice_id)

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
    invoice = TurkeyHotel(data=payload)

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
    invoice = await session.get(TurkeyHotel, invoice_id)

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
    invoice = await session.get(TurkeyHotel, invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    await session.delete(invoice)
    await session.commit()

    return {
        "success": True,
        "message": "Invoice deleted successfully"
    }
