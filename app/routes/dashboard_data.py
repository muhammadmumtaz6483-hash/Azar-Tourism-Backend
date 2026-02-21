from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db

from routes.services.invoice_service import get_all_invoice_records
from routes.services.turkey_hotel_service import get_all_turkey_hotels
from routes.services.egypt_hotel_service import get_all_egypt_hotels    

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)

@router.get("/", status_code=status.HTTP_200_OK)
async def dashboard_data(db: AsyncSession = Depends(get_db)):
    invoices_data = await get_all_invoice_records(db)
    turkey_hotels_data = await get_all_turkey_hotels(db)
    egypt_hotels_data = await get_all_egypt_hotels(db)      

    return {
        "success": True,
        "message": "Dashboard data loaded successfully",
        "data": {
            "invoices": invoices_data,
            "turkey_hotels": turkey_hotels_data,
            "egypt_hotels": egypt_hotels_data       
        }
    }
