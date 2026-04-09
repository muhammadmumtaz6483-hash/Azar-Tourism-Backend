from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.dubai_hotel import DubaiHotel

async def get_all_dubai_hotels(db: AsyncSession):
    result = await db.execute(select(DubaiHotel ))
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }

async def get_all_dubai_hotels_by_page(db: AsyncSession, offset: int, limit: int):
    query = select(DubaiHotel).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }
