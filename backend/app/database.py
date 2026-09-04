from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from app.config import settings
import logging

logger = logging.getLogger("database")

class DatabaseContainer:
    def __init__(self):
        self.client = None
        self.db = None

    def get_db(self):
        if self.db is None:
            raise RuntimeError("Database connection has not been initialized. Please verify MongoDB connection configuration.")
        return self.db

db_container = DatabaseContainer()

async def connect_to_mongo():
    try:
        mongo_uri = settings.MONGODB_URI or settings.MONGODB_URL
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Verify connection with ping
        await client.admin.command('ping')
        
        db_container.client = client
        db_container.db = client[settings.DATABASE_NAME]
        
        # Initialize required indexes across all 7 collections
        await db_container.db.users.create_index([("email", ASCENDING)], unique=True)
        await db_container.db.inspections.create_index([("inspection_id", ASCENDING)], unique=True)
        await db_container.db.inspections.create_index([("user_id", ASCENDING)])
        await db_container.db.inspections.create_index([("created_at", DESCENDING)])
        await db_container.db.inspections.create_index([("status", ASCENDING)])
        await db_container.db.ocr_results.create_index([("inspection_id", ASCENDING)])
        await db_container.db.compliance_results.create_index([("inspection_id", ASCENDING)])
        await db_container.db.guidelines.create_index([("rule_id", ASCENDING)])
        await db_container.db.contact_messages.create_index([("ticket_id", ASCENDING)])
        await db_container.db.password_reset_tokens.create_index([("email", ASCENDING)])
        
        # Log safe confirmation (Never log credentials, URLs, or secrets)
        logger.info("MongoDB Atlas connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise RuntimeError("MongoDB connection failed. Backend startup aborted.") from e

async def close_mongo_connection():
    if db_container.client:
        db_container.client.close()

def get_database():
    return db_container.get_db()

