import asyncio
from app.database import get_database, connect_to_mongo
from app.config import settings

async def main():
    await connect_to_mongo(settings.MONGO_URI)
    db = get_database()
    doc = await db.inspections.find_one()
    print(doc['inspection_id'] if doc else 'None')

if __name__ == "__main__":
    asyncio.run(main())
