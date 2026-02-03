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
