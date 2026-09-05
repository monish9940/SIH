import asyncio
import time
import os
import sys
from fastapi.testclient import TestClient

# Ensure root backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import connect_to_mongo, get_database
from app.services.auth_service import create_access_token
from app.services.ocr_service import get_easyocr_reader

async def run_async_analysis_test():
    print("=== STARTING ASYNC ANALYSIS TEST ===")
    await connect_to_mongo()

    # Ensure EasyOCR is prewarmed
    print("Initializing EasyOCR reader...")
    reader = get_easyocr_reader()
    assert reader is not None, "EasyOCR reader failed to initialize"
    print("EasyOCR reader ready.")

    db = get_database()
    await db.users.update_one(
        {"user_id": "OFFICER_A"},
        {"$set": {"user_id": "OFFICER_A", "email": "officera@gov.in", "full_name": "Officer A", "role": "officer"}},
        upsert=True
    )
    await db.users.update_one(
        {"user_id": "OFFICER_B"},
        {"$set": {"user_id": "OFFICER_B", "email": "officerb@gov.in", "full_name": "Officer B", "role": "officer"}},
        upsert=True
    )

    # Create tokens for User A (owner) and User B (unauthorized)
    token_a = create_access_token({"sub": "Officer A", "user_id": "OFFICER_A", "role": "officer"})
    token_b = create_access_token({"sub": "Officer B", "user_id": "OFFICER_B", "role": "officer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    sample_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_label.jpg")
    assert os.path.exists(sample_img_path), "sample_label.jpg missing for test"

    with TestClient(app) as client:
        # 1. Test Health endpoint
        health_res = client.get("/api/health")
        print(f"Health response: {health_res.status_code} {health_res.json()}")
        assert health_res.status_code == 200
        assert health_res.json()["ocr_ready"] is True

        # 2. Create Inspection (201 Created)
        with open(sample_img_path, "rb") as f:
            create_res = client.post(
                "/api/inspections",
                files={"file": ("sample_label.jpg", f, "image/jpeg")},
                data={"commodity_type": "Food & Beverages", "inspection_profile": "Standard PCR Rules 2011"},
                headers=headers_a
            )
        print(f"Create response: {create_res.status_code} {create_res.json()}")
        assert create_res.status_code == 201
        inspection_id = create_res.json()["inspection_id"]
        print(f"Created inspection_id: {inspection_id}")

        # 3. Trigger Analyze (Expect 202 Accepted quickly)
        t0 = time.time()
        analyze_res = client.post(f"/api/inspections/{inspection_id}/analyze", headers=headers_a)
        duration = time.time() - t0
        print(f"Analyze response: {analyze_res.status_code} | duration: {duration:.3f}s | body: {analyze_res.json()}")
        assert analyze_res.status_code == 202
        assert analyze_res.json()["status"] == "PROCESSING"
        assert duration < 2.0, f"Analyze HTTP response took too long: {duration:.3f}s"

        # 4. Duplicate Analyze Guard
        dup_res = client.post(f"/api/inspections/{inspection_id}/analyze", headers=headers_a)
        print(f"Duplicate analyze response: {dup_res.status_code} | body: {dup_res.json()}")
        assert dup_res.status_code == 202
        assert dup_res.json()["status"] == "PROCESSING"

        # 5. Ownership Guard Check (User B trying to access User A's status or analyze)
        forbidden_status = client.get(f"/api/inspections/{inspection_id}/analysis-status", headers=headers_b)
        print(f"User B status check: {forbidden_status.status_code}")
        assert forbidden_status.status_code == 403

        forbidden_analyze = client.post(f"/api/inspections/{inspection_id}/analyze", headers=headers_b)
        print(f"User B analyze trigger: {forbidden_analyze.status_code}")
        assert forbidden_analyze.status_code == 403

        # 6. Poll Status Endpoint until COMPLETED
        print("Polling analysis-status endpoint...")
        poll_count = 0
        final_result = None
        for _ in range(60): # Up to 30s polling
            await asyncio.sleep(0.5)
            poll_count += 1
            status_res = client.get(f"/api/inspections/{inspection_id}/analysis-status", headers=headers_a)
            assert status_res.status_code == 200
            data = status_res.json()
            curr_status = data.get("status")
            print(f"Poll #{poll_count}: status = {curr_status}")
            if curr_status == "COMPLETED":
                final_result = data.get("result")
                break
            elif curr_status == "FAILED":
                raise RuntimeError(f"Background analysis failed: {data.get('error')}")

        assert final_result is not None, "Analysis did not complete within timeout"
        assert final_result["analyzed"] is True
        assert "product_information" in final_result
        assert "compliance_score" in final_result
        print("Background analysis completed successfully!")
        print(f"Product Name: {final_result['product_information'].get('product_name')}")
        print(f"MRP: {final_result['product_information'].get('mrp')}")
        print(f"Score: {final_result.get('compliance_score')}")

        # 7. Test PDF Endpoint for completed inspection
        pdf_res = client.get(f"/api/inspections/{inspection_id}/pdf", headers=headers_a)
        print(f"PDF Response: {pdf_res.status_code} | content-type: {pdf_res.headers.get('content-type')}")
        assert pdf_res.status_code == 200
        assert pdf_res.headers.get("content-type") == "application/pdf"
        assert len(pdf_res.content) > 1000

    print("=== ASYNC ANALYSIS TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_async_analysis_test())
