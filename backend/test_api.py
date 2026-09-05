import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.database import connect_to_mongo
from app.config import settings
from app.services.auth_service import create_access_token

async def run_test():
    await connect_to_mongo()
    
    # Create a valid token
    token = create_access_token({"sub": "admin", "user_id": "U12345", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # We need a valid inspection_id
    from app.database import get_database
    db = get_database()
    inspection = await db.inspections.find_one({"status": "NEEDS_REVIEW"})
    if not inspection:
        print("No inspection found.")
        return
        
    inspection_id = inspection["inspection_id"]
    print(f"Testing analyze for {inspection_id}...")
    
    with TestClient(app) as client:
        health_res = client.get("/health")
        print("HEALTH STATUS:", health_res.status_code, health_res.json())
        response = client.post(f"/api/inspections/{inspection_id}/analyze", headers=headers)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

if __name__ == "__main__":
    asyncio.run(run_test())
