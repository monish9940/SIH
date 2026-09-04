import requests
import json
import os
import cv2
import numpy as np

BASE_URL = "http://127.0.0.1:8090/api"

def run_tests():
    print("==================================================")
    print("   PRODUCTION INTEGRATION TEST VERIFICATION      ")
    print("==================================================")

    # 1. User A Signup
    user_a_email = "inspector.rajesh@gov.in"
    user_a_signup = {
        "full_name": "Rajesh Kumar",
        "email": user_a_email,
        "phone": "9876543210",
        "organization_type": "State Legal Metrology Department",
        "password": "SecurePassword123!"
    }
    
    print("\n1. Testing User A Signup (POST /api/auth/signup)...")
    res = requests.post(f"{BASE_URL}/auth/signup", json=user_a_signup)
    if res.status_code == 201:
        print("  [OK] User A created successfully. Role:", res.json()["role"])
    elif res.status_code == 400:
        print("  [OK] User A already exists in MongoDB, proceeding to login...")
    else:
        raise AssertionError(f"Signup failed: {res.status_code} {res.text}")

    # 2. Testing Duplicate Signup Rejection
    print("\n2. Testing Duplicate Email Rejection...")
    res = requests.post(f"{BASE_URL}/auth/signup", json=user_a_signup)
    assert res.status_code == 400, f"Duplicate signup allowed unexpectedly: {res.text}"
    print("  [OK] Duplicate signup correctly rejected with HTTP 400.")

    # 3. Testing Invalid Password Login Rejection
    print("\n3. Testing Invalid Credentials Login Rejection...")
    invalid_login = {"email": user_a_email, "password": "WrongPassword!"}
    res = requests.post(f"{BASE_URL}/auth/login", json=invalid_login)
    assert res.status_code == 401, f"Invalid login allowed unexpectedly: {res.text}"
    print("  [OK] Invalid login correctly rejected with HTTP 401.")

    # 4. User A Valid Login
    print("\n4. Testing User A Login (POST /api/auth/login)...")
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": user_a_email, "password": "SecurePassword123!"})
    assert res.status_code == 200, f"User A login failed: {res.text}"
    token_a = res.json()["access_token"]
    user_a_data = res.json()["user"]
    print("  [OK] Login successful! JWT Token acquired.")
    print("  [OK] Authenticated Officer Name:", user_a_data["full_name"], f"(ID: {user_a_data['user_id']})")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 5. User A Current User Profile (/api/auth/me)
    print("\n5. Testing Get Current User Profile (GET /api/auth/me)...")
    res = requests.get(f"{BASE_URL}/auth/me", headers=headers_a)
    assert res.status_code == 200, f"Get me failed: {res.text}"
    assert res.json()["email"] == user_a_email
    print("  [OK] Profile Verified:", res.json()["full_name"], f"({res.json()['email']})")

    # 6. User B Signup & Login (for Cross-Officer Authorization Testing)
    user_b_email = "inspector.anita@gov.in"
    user_b_signup = {
        "full_name": "Anita Sharma",
        "email": user_b_email,
        "phone": "9123456789",
        "organization_type": "District Legal Metrology Office",
        "password": "SecurePassword456!"
    }
    print("\n6. Setting up User B for Cross-Officer Security Verification...")
    res = requests.post(f"{BASE_URL}/auth/signup", json=user_b_signup)
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": user_b_email, "password": "SecurePassword456!"})
    assert res.status_code == 200, "User B login failed."
    token_b = res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    print("  [OK] User B Token acquired:", res.json()["user"]["full_name"])

    # 7. Create Test Label Image
    sample_img_path = "sample_label.jpg"
    img = np.ones((400, 600, 3), dtype=np.uint8) * 240
    cv2.putText(img, "POTATO CHIPS PACKET", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (15, 25, 44), 2)
    cv2.putText(img, "CRISP CHIPS", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (15, 25, 44), 2)
    cv2.putText(img, "NET QTY: 50 G", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (22, 163, 74), 2)
    cv2.putText(img, "MRP: RS. 20.00 INCL TAXES", (50, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (22, 163, 74), 2)
    cv2.putText(img, "MFG DATE: 01/2026", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (15, 25, 44), 2)
    cv2.putText(img, "MFD BY: QUALITY PACKAGERS PVT LTD", (50, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (15, 25, 44), 1)
    cv2.imwrite(sample_img_path, img)

    # 8. User A Creates New Inspection
    print("\n7. Testing User A Create Inspection (POST /api/inspections)...")
    with open(sample_img_path, "rb") as f:
        files = {"file": ("sample_label.jpg", f, "image/jpeg")}
        data = {"commodity_type": "Food & Beverages", "inspection_profile": "Standard PCR Rules 2011"}
        res = requests.post(f"{BASE_URL}/inspections", headers=headers_a, files=files, data=data)
    assert res.status_code == 201, f"Create inspection failed: {res.text}"
    insp_id_a = res.json()["inspection_id"]
    print("  [OK] Created Inspection ID for User A:", insp_id_a)

    # 9. User A Triggers OCR & Compliance Analysis
    print(f"\n8. Testing User A Analysis (POST /api/inspections/{insp_id_a}/analyze)...")
    res = requests.post(f"{BASE_URL}/inspections/{insp_id_a}/analyze", headers=headers_a)
    assert res.status_code == 200, f"Analysis failed: {res.text}"
    analysis = res.json()
    print("  [OK] Score:", f"{analysis['compliance_score']}%", "| Status:", analysis['overall_status'])

    # VERIFY ABSENCE OF FORBIDDEN MOCK STRINGS
    json_str = json.dumps(analysis)
    assert "Kama Foods" not in json_str, "Forbidden sample product 'Kama Foods' detected!"
    assert "Apex Foods" not in json_str, "Forbidden sample manufacturer 'Apex Foods' detected!"
    assert "525.00" not in json_str, "Forbidden sample price '525.00' detected!"

    # 10. Cross-Officer Authorization Test: User B Access Attempt on User A Inspection (Must Return HTTP 403)
    print(f"\n9. Testing Security: User B Attempting Access to User A Inspection ({insp_id_a})...")
    res = requests.get(f"{BASE_URL}/inspections/{insp_id_a}", headers=headers_b)
    assert res.status_code == 403, f"Security Violation! User B accessed User A inspection with status {res.status_code}"
    print("  [OK] HTTP 403 Forbidden returned correctly! Cross-officer inspection access blocked.")

    # 11. Cross-Officer PDF Download Attempt (Must Return HTTP 403)
    print(f"\n10. Testing Security: User B Attempting PDF Download of User A Inspection ({insp_id_a})...")
    res = requests.get(f"{BASE_URL}/inspections/{insp_id_a}/pdf", headers=headers_b)
    assert res.status_code == 403, f"Security Violation! User B downloaded User A PDF with status {res.status_code}"
    print("  [OK] HTTP 403 Forbidden returned correctly! Cross-officer PDF download blocked.")

    # 12. User A Retrieves Own Inspection
    print(f"\n11. Testing User A Retrieval of Own Inspection ({insp_id_a})...")
    res = requests.get(f"{BASE_URL}/inspections/{insp_id_a}", headers=headers_a)
    assert res.status_code == 200, f"Get inspection failed: {res.text}"
    print("  [OK] Inspection Product Name:", res.json()["product_information"]["product_name"])

    # 13. User A Generates & Downloads PDF Report
    print(f"\n12. Testing PDF Generation & Download (GET /api/inspections/{insp_id_a}/pdf)...")
    res = requests.get(f"{BASE_URL}/inspections/{insp_id_a}/pdf", headers=headers_a)
    assert res.status_code == 200, f"PDF download failed: {res.text}"
    assert res.headers["content-type"] == "application/pdf"
    print("  [OK] PDF Report Generated successfully! Size:", len(res.content), "bytes")

    # 14. Testing User-Isolated Dashboard Summary Metrics
    print("\n13. Testing User A Isolated Dashboard Summary (GET /api/dashboard/summary)...")
    res_summary_a = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers_a)
    assert res_summary_a.status_code == 200
    metrics_a = res_summary_a.json()
    print("  [OK] User A Dashboard Metrics:", metrics_a)

    print("\n14. Testing User B Isolated Dashboard Summary (GET /api/dashboard/summary)...")
    res_summary_b = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers_b)
    assert res_summary_b.status_code == 200
    metrics_b = res_summary_b.json()
    print("  [OK] User B Dashboard Metrics:", metrics_b)
    assert metrics_b["total_scans"] == 0, "User B should have 0 total scans."

    # 15. Testing Invalid Token Protection
    print("\n15. Testing Invalid JWT Token Request Rejection...")
    invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
    res = requests.get(f"{BASE_URL}/auth/me", headers=invalid_headers)
    assert res.status_code == 401, "Invalid token allowed unexpectedly."
    print("  [OK] Invalid token correctly rejected with HTTP 401.")

    # 16. Testing User A Complete Review (PATCH /api/inspections/{id}/complete-review)
    print(f"\n16. Testing User A Complete Manual Review (PATCH /api/inspections/{insp_id_a}/complete-review)...")
    review_notes = "Physical package inspected. All statutory declarations verified on site."
    res = requests.patch(
        f"{BASE_URL}/inspections/{insp_id_a}/complete-review",
        headers=headers_a,
        json={"officer_review_notes": review_notes}
    )
    assert res.status_code == 200, f"Complete review failed: {res.status_code} {res.text}"
    resolved_doc = res.json()
    assert resolved_doc["status"] == "RESOLVED", f"Expected status RESOLVED, got {resolved_doc['status']}"
    assert resolved_doc["officer_review_notes"] == review_notes
    assert "reviewed_at" in resolved_doc
    print("  [OK] Inspection successfully resolved! Status:", resolved_doc["status"])

    # 17. Testing User B Cross-Officer Complete Review Rejection (HTTP 403)
    print(f"\n17. Testing Security: User B Attempting Complete Review on User A Inspection...")
    res = requests.patch(
        f"{BASE_URL}/inspections/{insp_id_a}/complete-review",
        headers=headers_b,
        json={"officer_review_notes": "Unauthorized edit"}
    )
    assert res.status_code == 403, f"Security Violation! User B completed review with status {res.status_code}"
    print("  [OK] HTTP 403 Forbidden returned correctly! Cross-officer review completion blocked.")

    # 18. Testing Duplicate Complete Review Rejection (HTTP 400)
    print("\n18. Testing Re-completing Already Resolved Inspection Rejection...")
    res = requests.patch(
        f"{BASE_URL}/inspections/{insp_id_a}/complete-review",
        headers=headers_a,
        json={"officer_review_notes": "Duplicate completion"}
    )
    assert res.status_code == 400, f"Duplicate review completion allowed unexpectedly: {res.status_code}"
    print("  [OK] Duplicate completion correctly rejected with HTTP 400.")

    # 19. Testing Post-Resolution PDF Generation & Content
    print(f"\n19. Testing Post-Resolution PDF Download (GET /api/inspections/{insp_id_a}/pdf)...")
    res = requests.get(f"{BASE_URL}/inspections/{insp_id_a}/pdf", headers=headers_a)
    assert res.status_code == 200, f"Post-resolution PDF download failed: {res.text}"
    assert res.headers["content-type"] == "application/pdf"
    assert "Content-Disposition" in res.headers
    assert f"Compliance_Report_{insp_id_a}.pdf" in res.headers["Content-Disposition"]
    print("  [OK] Resolved PDF generated with header Attachment disposition! Size:", len(res.content), "bytes")

    # 20. Testing Dashboard Metrics After Resolution
    print("\n20. Testing User A Updated Dashboard Metrics (GET /api/dashboard/summary)...")
    res_summary_a2 = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers_a)
    assert res_summary_a2.status_code == 200
    metrics_a2 = res_summary_a2.json()
    assert metrics_a2["issues_resolved"] >= 1, f"Issues resolved not updated in MongoDB: {metrics_a2}"
    print("  [OK] User A Issues Resolved Metric Updated in MongoDB:", metrics_a2["issues_resolved"])

    print("\n==================================================")
    print("   ALL 20 INTEGRATION SECURITY TESTS PASSED (100%)")
    print("==================================================")

if __name__ == "__main__":
    run_tests()

