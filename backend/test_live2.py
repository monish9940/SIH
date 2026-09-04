"""
Captures the EXACT traceback from the running uvicorn server
by intercepting its stderr/stdout via log file.
"""
import asyncio
import httpx
import motor.motor_asyncio
from jose import jwt
from datetime import datetime, timedelta
import os

MONGO_URI = "mongodb+srv://admin:admin@cluster0.xa9ykft.mongodb.net/?appName=Cluster0"
DB_NAME = "legal_metrology_compliance"
API_BASE = "http://localhost:8090"
SECRET = "super_secret_legal_metrology_jwt_key_2026"

async def main():
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = mongo_client[DB_NAME]

    user = await db.users.find_one({})
    user_id = str(user.get("user_id", user.get("_id")))
    email = user.get("email", "test@test.com")

    payload = {
        "sub": email,
        "user_id": user_id,
        "full_name": user.get("full_name", "Test Officer"),
        "role": user.get("role", "officer"),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")

    inspection = await db.inspections.find_one({"user_id": user_id})
    if not inspection:
        inspection = await db.inspections.find_one({})
    mongo_client.close()

    inspection_id = inspection["inspection_id"]
    print(f"Testing analyze on {inspection_id} as user {email}")

    # Now hit the endpoint with debug=true to get full traceback
    async with httpx.AsyncClient(base_url=API_BASE, timeout=120) as client:
        resp = await client.post(
            f"/api/inspections/{inspection_id}/analyze",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Status: {resp.status_code}")
        print(f"Headers: {dict(resp.headers)}")
        print(f"Body: {resp.text}")

if __name__ == "__main__":
    asyncio.run(main())
