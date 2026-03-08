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
