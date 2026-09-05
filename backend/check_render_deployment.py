import urllib.request
import json
import time

url = "https://sih-b9dp.onrender.com/"
print(f"Monitoring Render deployment at {url}...")

for i in range(30):
    try:
        req = urllib.request.urlopen(url, timeout=10)
        body = req.read().decode('utf-8')
        data = json.loads(body)
        version = data.get("version")
        print(f"Attempt #{i+1}: status = {data.get('status')}, version = {version}")
        if version == "2026.09.05-v3":
            print("\n=== SUCCESS: RENDER HAS DEPLOYED VERSION v3! ===")
            print(json.dumps(data, indent=2))
            break
    except Exception as e:
        print(f"Attempt #{i+1}: error - {e}")
    time.sleep(5)
