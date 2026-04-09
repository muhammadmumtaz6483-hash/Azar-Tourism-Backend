from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.uk_hotel import UKHotel

async def get_all_uk_hotels(db: AsyncSession):
    result = await db.execute(select(UKHotel ))
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }

async def get_all_uk_hotels_by_page(db: AsyncSession, offset: int, limit: int):
    query = select(UKHotel).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }
