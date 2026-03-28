from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.tounis_hotel import TounisHotel

async def get_all_tounis_hotels(db: AsyncSession):
    result = await db.execute(select(TounisHotel ))
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }

async def get_all_tounis_hotels_by_page(db: AsyncSession, offset: int, limit: int):
    query = select(TounisHotel).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }
