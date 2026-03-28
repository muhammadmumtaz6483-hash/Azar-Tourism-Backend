from fastapi import APIRouter, Depends, status,Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
# from sqlalchemy import func, case, select
from models.egypt_hotel import EgyptHotel
from models.turkey_hotel import TurkeyHotel 
from sqlalchemy import select, func, case, union_all
from routes.services.invoice_service import get_all_invoice_records
from routes.services.turkey_hotel_service import get_all_turkey_hotels, get_all_turkey_hotels_by_page
from routes.services.egypt_hotel_service import get_all_egypt_hotels ,get_all_egypt_hotels_by_page  
from routes.services.malaysia_hotel_service import get_all_malaysia_hotels, get_all_malaysia_hotels_by_page

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)

@router.get("/", status_code=status.HTTP_200_OK)
async def dashboard_data(db: AsyncSession = Depends(get_db)):
    invoices_data = await get_all_invoice_records(db)
    turkey_hotels_data = await get_all_turkey_hotels(db)
    egypt_hotels_data = await get_all_egypt_hotels(db)  
    malaysia_hotels_data = await get_all_malaysia_hotels(db)    

    return {
        "success": True,
        "message": "Dashboard data loaded successfully",
        "data": {
            "invoices": invoices_data,
            "turkey_hotels": turkey_hotels_data,
            "egypt_hotels": egypt_hotels_data,
            "malaysia_hotels": malaysia_hotels_data     
        }
    }

# @router.get("/getbypage", status_code=status.HTTP_200_OK)
# async def dashboard_data(
#     page: int = Query(1, ge=1),
#     db: AsyncSession = Depends(get_db)
# ):
#     page_size = 10
#     offset = (page - 1) * page_size

#     # invoices_data = await get_all_invoice_records_by_page(db, offset, page_size)
#     turkey_hotels_data = await get_all_turkey_hotels_by_page(db, offset, page_size)
#     egypt_hotels_data = await get_all_egypt_hotels_by_page(db, offset, page_size)
#     malaysia_hotels_data = await get_all_malaysia_hotels_by_page(db, offset, page_size)

#     return {
#         "success": True,
#         "message": "Dashboard data loaded successfully",
#         "pagination": {
#             "page": page,
#             "page_size": page_size   
#         },
#         "data": {
#             # "invoices": invoices_data,
#             "turkey_hotels": turkey_hotels_data,
#             "egypt_hotels": egypt_hotels_data,
#             "malaysia_hotels": malaysia_hotels_data
#         }
#     }


# @router.get("/getbypagination", status_code=status.HTTP_200_OK)
# async def dashboard_data(
#     page: int = Query(1, ge=1),
#     db: AsyncSession = Depends(get_db)
# ):
#     page_size = 10
#     offset = (page - 1) * page_size

#     # ✅ Get ALL data (no pagination here)
#     invoices_data = await get_all_invoice_records(db)
#     turkey_hotels_data = await get_all_turkey_hotels(db)
#     egypt_hotels_data = await get_all_egypt_hotels(db)
#     malaysia_hotels_data = await get_all_malaysia_hotels(db)

#     # ✅ Extract records
#     all_records = (
#         invoices_data["records"] +
#         turkey_hotels_data["records"] +
#         egypt_hotels_data["records"] +
#         malaysia_hotels_data["records"]
#     )

#     # ✅ Sort by latest (IMPORTANT)
#     all_records.sort(key=lambda x: x.created_at, reverse=True)

#     # ✅ Apply pagination AFTER merge
#     paginated_data = all_records[offset: offset + page_size]

#     return {
#         "success": True,
#         "message": "Dashboard data loaded successfully",
#         "pagination": {
#             "page": page,
#             "page_size": page_size,
#             "total": len(all_records)
#         },
#         "data": paginated_data
#     }

# ✅ Correct nested status path
def status_expr(model):
    return func.lower(
        func.trim(
            func.coalesce(
                model.data["data"]["data"]["data"]["status"].astext,
                ""
            )
        )
    )


async def get_table_stats(db: AsyncSession, model):

    expr = status_expr(model)

    query = select(
        func.count().label("total"),

        func.sum(case((expr == "pending", 1), else_=0)).label("pending"),
        func.sum(case((expr == "completed", 1), else_=0)).label("completed"),
        func.sum(case((expr == "rejected", 1), else_=0)).label("rejected"),
        func.sum(case((expr == "ready", 1), else_=0)).label("ready"),
    )

    result = await db.execute(query)
    return result.one()


async def get_combined_dashboard_stats(db: AsyncSession):

    turkey = await get_table_stats(db, TurkeyHotel)
    egypt = await get_table_stats(db, EgyptHotel)

    return {
        "total": (turkey.total or 0) + (egypt.total or 0),
        "pending": (turkey.pending or 0) + (egypt.pending or 0),
        "completed": (turkey.completed or 0) + (egypt.completed or 0),
        "rejected": (turkey.rejected or 0) + (egypt.rejected or 0),
        "ready": (turkey.ready or 0) + (egypt.ready or 0),
    }


@router.get("/stats", status_code=status.HTTP_200_OK)
async def dashboard_stats(db: AsyncSession = Depends(get_db)):

    stats = await get_combined_dashboard_stats(db)

    return {
        "success": True,
        "message": "Combined dashboard stats loaded successfully",
        "data": stats
    }