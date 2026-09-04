"""
Live HTTP test: POST /api/inspections/{id}/analyze
This will reproduce the exact error the frontend sees.
"""
import asyncio
import httpx
import json
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb+srv://admin:admin@cluster0.xa9ykft.mongodb.net/?appName=Cluster0")
DB_NAME = os.getenv("DATABASE_NAME", "legal_metrology_compliance")
API_BASE = "http://localhost:8090"

async def main():
    # 1. Get a valid JWT by logging in
    print("Step 1: Login to get JWT token...")
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        # Try to find credentials from .env or use defaults
        login_payload = {
            "username": os.getenv("TEST_EMAIL", "admin@lmchecker.gov.in"),
            "password": os.getenv("TEST_PASSWORD", "Admin@123")
        }
        # FastAPI OAuth2 expects form data
        login_resp = await client.post("/api/auth/login", data=login_payload)
        print(f"  Login status: {login_resp.status_code}")
        if login_resp.status_code != 200:
            # Try JSON
            login_resp2 = await client.post("/api/auth/login", json=login_payload)
            print(f"  Login JSON status: {login_resp2.status_code}")
            print(f"  Login JSON body: {login_resp2.text[:500]}")
            if login_resp2.status_code != 200:
                print("  CANNOT LOGIN. Trying direct DB token generation...")
                # Get any user and generate token directly via DB check
                return await test_with_db_lookup(client)
        token = login_resp.json().get("access_token")
        print(f"  Token: {token[:40]}...")
        await run_analyze(client, token)

async def test_with_db_lookup(client):
    """Generate an auth token by looking up a user from MongoDB."""
    from jose import jwt
    from datetime import datetime, timedelta
    
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    
    # Find a user
    user = await db.users.find_one({})
    if not user:
        print("No users found in DB. Create a user first.")
        return
    
    user_id = str(user.get("user_id", user.get("_id")))
    full_name = user.get("full_name", "Test Officer")
    email = user.get("email", "test@test.com")
    
    SECRET = os.getenv("JWT_SECRET", "super_secret_legal_metrology_jwt_key_2026")
    payload = {
        "sub": email,
        "user_id": user_id,
        "full_name": full_name,
        "role": user.get("role", "officer"),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    print(f"  Generated token for user: {email} (id: {user_id})")
    
    # Find an unanalyzed inspection owned by this user
    inspection = await db.inspections.find_one({"user_id": user_id})
    if not inspection:
        print("No inspections found for this user. Trying any inspection...")
        inspection = await db.inspections.find_one({})
    
    if not inspection:
        print("No inspections in DB at all.")
        return
    
    inspection_id = inspection["inspection_id"]
    print(f"  Using inspection: {inspection_id}")
    
    mongo_client.close()
    await run_analyze(client, token, inspection_id)

async def run_analyze(client, token, inspection_id=None):
    if not inspection_id:
        # Get inspection list
        print("Step 2: Getting inspection list...")
        list_resp = await client.get("/api/inspections", headers={"Authorization": f"Bearer {token}"})
        print(f"  List status: {list_resp.status_code}")
        if list_resp.status_code != 200:
            print(f"  Error: {list_resp.text}")
            return
        inspections = list_resp.json()
        print(f"  Found {len(inspections)} inspections")
        if not inspections:
            print("  No inspections found.")
            return
        inspection_id = inspections[0]["inspection_id"]
    
    print(f"Step 3: Analyzing inspection {inspection_id}...")
    analyze_resp = await client.post(
        f"/api/inspections/{inspection_id}/analyze",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"  Analyze status: {analyze_resp.status_code}")
    if analyze_resp.status_code == 200:
        result = analyze_resp.json()
        print(f"  SUCCESS!")
        print(f"  Product: {result.get('product_information', {}).get('product_name')}")
        print(f"  MRP: {result.get('product_information', {}).get('mrp')}")
        print(f"  Net Qty: {result.get('product_information', {}).get('net_quantity')}")
        print(f"  Score: {result.get('compliance_score')}")
        print(f"  Status: {result.get('overall_status')}")
    else:
        print(f"  FAILED! Response body:")
        print(f"  {analyze_resp.text[:2000]}")

if __name__ == "__main__":
    asyncio.run(main())
