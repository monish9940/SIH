from fastapi import APIRouter
from app.database import get_database

router = APIRouter(prefix="/api/guidelines", tags=["Guidelines"])

@router.get("")
async def get_guidelines():
    db = get_database()
    cursor = db.guidelines.find({})
    items = []
    async for doc in cursor:
        doc.pop("_id", None)
        items.append(doc)
    return items
