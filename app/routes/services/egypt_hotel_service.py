from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.egypt_hotel import EgyptHotel

async def get_all_egypt_hotels(db: AsyncSession):
    result = await db.execute(select(EgyptHotel ))
    records = result.scalars().all()

    return {
        "count": len(records),
        "records": records
    }
