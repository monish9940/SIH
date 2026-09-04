"""
Backend health check — tests every route group without needing a real user session.
Checks: root, docs, auth endpoints (schema validation), dashboard (auth guard),
inspections list (auth guard), guidelines.
"""
import sys, json, time
sys.path.insert(0, '.')

try:
    import requests
except ImportError:
    import subprocess, sys as _sys
    subprocess.check_call([_sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

BASE = "http://localhost:8090"
PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results = []

def check(tag, method, url, expected_status, body=None, headers=None, label=None):
    label = label or f"{method} {url}"
    try:
        t0 = time.time()
        resp = requests.request(method, BASE + url, json=body, headers=headers or {}, timeout=10)
        elapsed = round(time.time() - t0, 3)
        ok = resp.status_code == expected_status
        tag_str = PASS if ok else FAIL
        try:
            resp_json = resp.json()
        except Exception:
            resp_json = resp.text[:120]
        print(f"  [{tag_str}] {label}")
        print(f"         status={resp.status_code} (expected {expected_status})  time={elapsed}s")
        if not ok:
            print(f"         body={json.dumps(resp_json)[:200]}")
        results.append(ok)
        return resp
    except Exception as e:
        print(f"  [{FAIL}] {label}: ERROR — {e}")
        results.append(False)
        return None

print("\n" + "="*60)
print("BACKEND HEALTH CHECK")
print("="*60)

# 1. Root
print("\n[1] Core API")
check("root", "GET", "/", 200, label="GET /  (root status)")

# 2. OpenAPI docs (FastAPI auto-generated)
print("\n[2] OpenAPI Docs")
check("docs", "GET", "/docs", 200, label="GET /docs  (Swagger UI)")
check("openapi", "GET", "/openapi.json", 200, label="GET /openapi.json  (OpenAPI schema)")

# 3. Auth endpoints — schema validation
print("\n[3] Auth Routes")
check("signup_missing", "POST", "/api/auth/signup", 422, label="POST /signup  (missing body → 422)")
check("login_bad", "POST", "/api/auth/login", 401,
      body={"email": "nobody@example.com", "password": "wrongpass"},
      label="POST /login  (invalid creds → 401)")
check("login_missing", "POST", "/api/auth/login", 422, label="POST /login  (missing body → 422)")

# 4. Protected routes — no token → 401/403
print("\n[4] Protected Routes (no token → 401)")
check("insp_list_noauth", "GET", "/api/inspections", 401, label="GET /inspections  (no auth → 401)")
check("dashboard_noauth", "GET", "/api/dashboard/summary", 401, label="GET /dashboard/summary  (no auth → 401)")
check("dashboard_trends", "GET", "/api/dashboard/trends", 401, label="GET /dashboard/trends  (no auth → 401)")
check("dashboard_res", "GET", "/api/dashboard/resolution-status", 401, label="GET /dashboard/resolution-status  (no auth → 401)")
check("insp_analyze_noauth", "POST", "/api/inspections/FAKE-123/analyze", 401,
      label="POST /inspections/FAKE/analyze  (no auth → 401)")
check("pdf_noauth", "GET", "/api/inspections/FAKE-123/pdf", 401,
      label="GET /inspections/FAKE/pdf  (no auth → 401)")
check("review_noauth", "PATCH", "/api/inspections/FAKE-123/complete-review", 401,
      label="PATCH /inspections/FAKE/complete-review  (no auth → 401)")

# 5. Guidelines (public)
print("\n[5] Guidelines (public)")
r = check("guidelines", "GET", "/api/guidelines", 200, label="GET /guidelines  (public)")
if r and r.status_code == 200:
    try:
        data = r.json()
        print(f"         returns {len(data)} guidelines")
    except Exception:
        pass

# 6. Contact (public POST)
print("\n[6] Contact")
check("contact_valid", "POST", "/api/contact", 201,
      body={"name": "Test Officer", "email": "officer@test.gov.in", "phone": "9876543210",
            "subject": "Test Query", "message": "Backend health check test message."},
      label="POST /contact  (valid incl. phone → 201)")
check("contact_missing", "POST", "/api/contact", 422, label="POST /contact  (missing body → 422)")

# 7. Static file serving
print("\n[7] Static File Serving")
check("uploads_static", "GET", "/uploads/", 404, label="GET /uploads/  (dir listing disabled → 404)")

# 8. Inspect OpenAPI schema for all registered routes
print("\n[8] Route Inventory (from OpenAPI schema)")
try:
    schema = requests.get(BASE + "/openapi.json", timeout=5).json()
    paths = sorted(schema.get("paths", {}).keys())
    print(f"  Total routes registered: {len(paths)}")
    for path in paths:
        methods = [m.upper() for m in schema["paths"][path].keys() if m != "parameters"]
        print(f"    {', '.join(methods):<10}  {path}")
except Exception as e:
    print(f"  Could not read OpenAPI schema: {e}")

# Summary
print(f"\n{'='*60}")
passed = sum(results)
total  = len(results)
status = "ALL PASS" if passed == total else f"{total-passed} FAILED"
print(f"RESULT: {passed}/{total} checks passed  — {status}")
