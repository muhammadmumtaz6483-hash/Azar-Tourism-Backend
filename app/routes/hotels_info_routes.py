from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.hotels_info import HotelsInfo

router = APIRouter(
    prefix="/api/hotel-info",
    tags=["Hotel Info"]
)

@router.post("/")
async def create_hotel_invoice(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    try:
        conditional = payload.get("conditional_sections", {})

        invoice = HotelsInfo(
            hotel_name=payload.get("hotel_name"),
            currency=payload.get("currency"),
            form_fields=payload.get("form_fields"),

            accommodation_details=conditional.get("accommodation_details"),
            city_tax=conditional.get("city_tax"),
            stamp_tax=conditional.get("stamp_tax"),
            other_services=conditional.get("other_services"),

            final_calculations=payload.get("final_calculations")
        )

        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)

        return {
            "message": "Hotel created successfully",
            "id": invoice.id
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/")
async def get_all_hotel_invoices(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(HotelsInfo))
        invoices = result.scalars().all()

        data = []
        for inv in invoices:
            reconstructed = {
                "id": inv.id, 
                "hotel_name": inv.hotel_name,
                "currency": inv.currency,
                "form_fields": inv.form_fields or [],
                "conditional_sections": {
                    "accommodation_details": inv.accommodation_details or {},
                    "city_tax": inv.city_tax or {},
                    "stamp_tax": inv.stamp_tax or {},
                    "other_services": inv.other_services or {}
                },
                "final_calculations": inv.final_calculations or {},
                "created_at": inv.created_at
            }
            data.append(reconstructed)

        return {
            "count": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/{invoice_id}")
async def get_hotel_invoice_by_id(invoice_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(HotelsInfo).where(HotelsInfo.id == invoice_id)
        )
        inv = result.scalar_one_or_none()

        if not inv:
            raise HTTPException(status_code=404, detail="Hotel not found")

        # Reconstruct JSON like original payload
        reconstructed = {
            "id": inv.id, 
            "hotel_name": inv.hotel_name,
            "currency": inv.currency,
            "form_fields": inv.form_fields or [],
            "conditional_sections": {
                "accommodation_details": inv.accommodation_details or {},
                "city_tax": inv.city_tax or {},
                "stamp_tax": inv.stamp_tax or {},
                "other_services": inv.other_services or {}
            },
            "final_calculations": inv.final_calculations or {},
            "created_at": inv.created_at
        }

        return reconstructed

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-hotel/{hotel_name}")
async def get_invoices_by_hotel_name(hotel_name: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(HotelsInfo).where(HotelsInfo.hotel_name.ilike(f"%{hotel_name}%"))
        )
        invoices = result.scalars().all()

        if not invoices:
            raise HTTPException(status_code=404, detail="No Hotels found for this hotel")

        data = []
        for inv in invoices:
            reconstructed = {
                "id": inv.id, 
                "hotel_name": inv.hotel_name,
                "currency": inv.currency,
                "form_fields": inv.form_fields or [],
                "conditional_sections": {
                    "accommodation_details": inv.accommodation_details or {},
                    "city_tax": inv.city_tax or {},
                    "stamp_tax": inv.stamp_tax or {},
                    "other_services": inv.other_services or {}
                },
                "final_calculations": inv.final_calculations or {},
                "created_at": inv.created_at
            }
            data.append(reconstructed)

        return {"count": len(data), "data": data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{invoice_id}")
async def update_hotel_invoice(invoice_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    try:
        # Fetch existing invoice
        result = await db.execute(
            select(HotelsInfo).where(HotelsInfo.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404, detail="Hotel not found")

        # Update top-level fields
        invoice.hotel_name = payload.get("hotel_name", invoice.hotel_name)
        invoice.currency = payload.get("currency", invoice.currency)
        invoice.form_fields = payload.get("form_fields", invoice.form_fields)
        invoice.final_calculations = payload.get("final_calculations", invoice.final_calculations)

        # Update conditional sections safely
        conditional = payload.get("conditional_sections", {})

        invoice.accommodation_details = conditional.get("accommodation_details", invoice.accommodation_details)
        invoice.city_tax = conditional.get("city_tax", invoice.city_tax)
        invoice.stamp_tax = conditional.get("stamp_tax", invoice.stamp_tax)
        invoice.other_services = conditional.get("other_services", invoice.other_services)

        # Commit changes
        await db.commit()
        await db.refresh(invoice)

        # Return reconstructed JSON
        updated_data = {
            "hotel_name": invoice.hotel_name,
            "currency": invoice.currency,
            "form_fields": invoice.form_fields or [],
            "conditional_sections": {
                "accommodation_details": invoice.accommodation_details or {},
                "city_tax": invoice.city_tax or {},
                "stamp_tax": invoice.stamp_tax or {},
                "other_services": invoice.other_services or {}
            },
            "final_calculations": invoice.final_calculations or {},
            "created_at": invoice.created_at
        }

        return {"message": "Hotel updated successfully", "data": updated_data}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/{invoice_id}")
async def delete_hotel_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(HotelsInfo).where(HotelsInfo.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(
                status_code=404,
                detail="Hotel not found"
            )

        await db.delete(invoice)
        await db.commit()

        return {
            "message": "Hotel deleted successfully",
            "invoice_id": invoice_id
        }

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
