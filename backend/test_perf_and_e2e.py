import requests
import time
import os

BASE_URL = "http://127.0.0.1:8090"

def run_tests():
    print("==================================================")
    print("   PERFORMANCE & E2E FUNCTIONAL VERIFICATION     ")
    print("==================================================")

    # 1. Login
    login_payload = {
        "email": "inspector.kumar@gov.in",
        "password": "Officer@123"
    }
    
    t0 = time.time()
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    t_login = (time.time() - t0) * 1000
    
    if login_res.status_code != 200:
        # Fallback to signup if not existing
        signup_payload = {
            "full_name": "Inspector Rajesh Kumar",
            "email": "inspector.kumar@gov.in",
            "password": "Officer@123",
            "mobile": "9876543210",
            "organization_type": "State Enforcement Agency"
        }
        requests.post(f"{BASE_URL}/api/auth/signup", json=signup_payload)
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)

    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[OK] Login successful ({t_login:.1f} ms). Token acquired.")

    # 2. Get User Profile /me
    t0 = time.time()
    me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    t_me = (time.time() - t0) * 1000
    assert me_res.status_code == 200
    print(f"[OK] GET /auth/me successful ({t_me:.1f} ms). Officer: {me_res.json()['full_name']}")

    # 3. Parallelized Dashboard Endpoints Performance Test
    t0 = time.time()
    sum_res = requests.get(f"{BASE_URL}/api/dashboard/summary", headers=headers)
    t_sum = (time.time() - t0) * 1000
    assert sum_res.status_code == 200
    print(f"[OK] GET /dashboard/summary ({t_sum:.1f} ms): {sum_res.json()}")

    t0 = time.time()
    trend_res = requests.get(f"{BASE_URL}/api/dashboard/trends", headers=headers)
    t_trend = (time.time() - t0) * 1000
    assert trend_res.status_code == 200
    print(f"[OK] GET /dashboard/trends ({t_trend:.1f} ms, 7 days parallelized): count={len(trend_res.json())}")

    t0 = time.time()
    res_res = requests.get(f"{BASE_URL}/api/dashboard/resolution-status", headers=headers)
    t_res = (time.time() - t0) * 1000
    assert res_res.status_code == 200
    print(f"[OK] GET /dashboard/resolution-status ({t_res:.1f} ms): {res_res.json()}")

    # 4. New Inspection Creation
    image_path = "e:/sih/backend/uploads/sample_lays.jpg"
    if not os.path.exists(image_path):
        # find any image in uploads
        uploads = [os.path.join("e:/sih/backend/uploads", f) for f in os.listdir("e:/sih/backend/uploads") if f.endswith((".jpg", ".png"))]
        image_path = uploads[0] if uploads else None

    assert image_path and os.path.exists(image_path), "No test image found"

    t0 = time.time()
    with open(image_path, "rb") as f:
        files = {"file": ("test_label.jpg", f, "image/jpeg")}
        data = {
            "commodity_type": "General Pre-packaged Goods",
            "inspection_profile": "Standard PCR Rules 2011"
        }
        create_res = requests.post(f"{BASE_URL}/api/inspections", headers=headers, files=files, data=data)
    t_create = (time.time() - t0) * 1000
    assert create_res.status_code == 201, f"Create inspection failed: {create_res.text}"
    insp_id = create_res.json()["inspection_id"]
    print(f"[OK] POST /api/inspections created ({t_create:.1f} ms): {insp_id}")

    # 5. OCR & Compliance Analysis
    t0 = time.time()
    analyze_res = requests.post(f"{BASE_URL}/api/inspections/{insp_id}/analyze", headers=headers)
    t_analyze = (time.time() - t0) * 1000
    assert analyze_res.status_code == 200, f"Analysis failed: {analyze_res.text}"
    print(f"[OK] POST /api/inspections/{insp_id}/analyze ({t_analyze:.1f} ms). Status: {analyze_res.json()['overall_status']}")

    # 6. Fetch Inspection Details
    t0 = time.time()
    detail_res = requests.get(f"{BASE_URL}/api/inspections/{insp_id}", headers=headers)
    t_detail = (time.time() - t0) * 1000
    assert detail_res.status_code == 200
    print(f"[OK] GET /api/inspections/{insp_id} ({t_detail:.1f} ms). Checks: {len(detail_res.json()['compliance_checks'])}")

    # 7. Complete Officer Manual Review
    review_payload = {
        "notes": "Verified package declarations physically against standard weights and measures rules."
    }
    t0 = time.time()
    review_res = requests.patch(f"{BASE_URL}/api/inspections/{insp_id}/complete-review", headers=headers, json=review_payload)
    t_review = (time.time() - t0) * 1000
    assert review_res.status_code == 200
    print(f"[OK] PATCH /api/inspections/{insp_id}/complete-review ({t_review:.1f} ms). Status: {review_res.json()['status']}")

    # 8. Inspection History Query
    t0 = time.time()
    hist_res = requests.get(f"{BASE_URL}/api/inspections?limit=50", headers=headers)
    t_hist = (time.time() - t0) * 1000
    assert hist_res.status_code == 200
    print(f"[OK] GET /api/inspections?limit=50 ({t_hist:.1f} ms). Records: {len(hist_res.json())}")

    # 9. PDF Generation & Download
    t0 = time.time()
    pdf_res = requests.get(f"{BASE_URL}/api/inspections/{insp_id}/pdf", headers=headers)
    t_pdf = (time.time() - t0) * 1000
    assert pdf_res.status_code == 200
    assert pdf_res.headers.get("content-type") == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")
    print(f"[OK] GET /api/inspections/{insp_id}/pdf ({t_pdf:.1f} ms). Received {len(pdf_res.content)} bytes PDF.")

    print("\n==================================================")
    print("   ALL PERFORMANCE & E2E TESTS PASSED 100%       ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
