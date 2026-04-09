from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.malaysia_hotel import MalaysiaHotel

async def get_all_malaysia_hotels(db: AsyncSession):
    result = await db.execute(select(MalaysiaHotel ))
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }

async def get_all_malaysia_hotels_by_page(db: AsyncSession, offset: int, limit: int):
    query = select(MalaysiaHotel).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "count": len(records),   
        "records": records
    }
