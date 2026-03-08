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
