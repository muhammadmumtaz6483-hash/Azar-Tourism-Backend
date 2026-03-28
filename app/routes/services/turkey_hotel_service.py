from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.turkey_hotel import TurkeyHotel

async def get_all_turkey_hotels(db: AsyncSession):
    result = await db.execute(select(TurkeyHotel))
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }

async def get_all_turkey_hotels_by_page(db: AsyncSession, offset: int, limit: int):
    query = select(TurkeyHotel).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }
