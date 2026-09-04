import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

guideline_data = [
    {
        "section_id": "sec-1",
        "num": "01",
        "title": "General Requirements",
        "category": "GENERAL",
        "requirements": [
            "A package intended for retail sale should carry mandatory declarations clearly.",
            "Declarations must be legible and in conspicuous font.",
            "Labels must be securely affixed to the package."
        ]
    },
    {
        "section_id": "sec-2",
        "num": "02",
        "title": "Mandatory Package Declarations",
        "category": "MANDATORY",
        "requirements": [
            "Manufacturer/Packer Name & Address",
            "Commodity Generic Name",
            "Net Quantity in SI units",
            "MRP inclusive of all taxes",
            "Month & Year of Manufacture",
            "Consumer Care Details"
        ]
    }
]

async def seed():
    print(f"Connecting to MongoDB: {settings.MONGODB_URL}...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    await db.guidelines.delete_many({})
    await db.guidelines.insert_many(guideline_data)
    print("Seed data successfully inserted into guidelines collection.")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
