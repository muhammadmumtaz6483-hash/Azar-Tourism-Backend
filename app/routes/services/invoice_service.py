from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.novotel_model import Invoice,AccommodationDetail,CityTaxDetail,StampTaxDetail,OtherService


async def get_all_invoice_records(db: AsyncSession):
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

    complete_records = []

    for invoice in invoices:
        invoice_dict = {
            col.name: (
                getattr(invoice, col.name).isoformat()
                if hasattr(getattr(invoice, col.name), "isoformat")
                else float(getattr(invoice, col.name))
                if isinstance(getattr(invoice, col.name), (int, float))
                else getattr(invoice, col.name)
            )
            for col in invoice.__table__.columns
        }

        complete_records.append({
            "invoice": invoice_dict,
            "accommodation_details": invoice.accommodation_details,
            "city_tax_details": invoice.city_tax_details,
            "stamp_tax_details": invoice.stamp_tax_details,
            "other_services": invoice.other_services
        })

    return {
        "invoice_count": len(invoices),
        "records": complete_records
    }
