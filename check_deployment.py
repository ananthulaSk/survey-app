import requests
import time

URL = "https://survey-app-171882639078.asia-south1.run.app/static/index.html"

def check_deployment():
    print(f"Fetching {URL}...")
    try:
        # Add a random query param to bypass some caches
        resp = requests.get(f"{URL}?t={time.time()}")
        print(f"Status: {resp.status_code}")
        
        content = resp.text
        if "DYNAMIC BASE HREF" in content:
            print("[SUCCESS] New Code FOUND on Server!", flush=True)
            print("Snippet:", content[:300])
        else:
            print("[FAIL] New Code NOT FOUND. Server is serving old version.", flush=True)
            print("Snippet:", content[:300])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_deployment()
