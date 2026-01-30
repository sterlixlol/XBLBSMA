#!/usr/bin/env python3
"""
Xiaomi Stats Checker
Verifies if the Ghost Farmer is actually working by checking user profile stats.
"""
import requests
import json
import os
from pathlib import Path

# ================= CONFIGURATION =================
SCRIPT_DIR = Path(__file__).parent.absolute()
TOKENS_FILE = SCRIPT_DIR / "TOKENS_BACKUP.json"
BASE_URL = "https://sgp-api.buy.mi.com/bbs/api/global"

def load_headers():
    """Load headers from TOKENS_BACKUP.json"""
    if not TOKENS_FILE.exists():
        print("❌ TOKENS_BACKUP.json not found!")
        print("   Copy TOKENS_BACKUP.example.json to TOKENS_BACKUP.json and fill in your tokens.")
        return None
    
    with open(TOKENS_FILE) as f:
        data = json.load(f)
    
    auth = data.get("authentication", {})
    device = data.get("device", {})
    
    token = auth.get("new_bbs_serviceToken", "")
    csrf = auth.get("x-csrf-token", "")
    device_id = device.get("deviceId", "")
    version_code = device.get("versionCode", "500429")
    version_name = device.get("versionName", "5.4.29")
    
    headers = {
        "Host": "sgp-api.buy.mi.com",
        "Cookie": f"new_bbs_serviceToken={token};versionCode={version_code};versionName={version_name};deviceId={device_id};",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/4.12.0"
    }
    
    if csrf:
        headers["x-csrf-token"] = csrf
    
    return headers

HEADERS = load_headers()

def check_stats():
    if HEADERS is None:
        return
    
    url = f"{BASE_URL}/user/data"
    print(f"📡 Querying {url}...")
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        print(f"📶 HTTP Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            code = data.get('code')
            
            if code == 0:
                user_info = data.get('data', {})
                level_info = user_info.get('level_info', {})
                
                print("\n📊 USER STATS:")
                print(f"   Name:   {user_info.get('user_name')}")
                print(f"   Level:  {level_info.get('level')} ({level_info.get('level_title')})")
                print(f"   Points: {user_info.get('point')}")
                print(f"   XP:     {level_info.get('current_value')} / {level_info.get('max_value')}")
                print(f"   Comments: {user_info.get('comment_count')}")
                print("\n✅ Token is VALID!")
            else:
                print(f"\n❌ API Error Code: {code}")
                print(f"   Message: {data.get('message', 'No message')}")
                print(f"\n🔍 Full Response:")
                print(json.dumps(data, indent=2))
                
                if code == 401 or code == -1:
                    print("\n⚠️  Token may be EXPIRED! You might need to re-extract via mitmproxy.")
        else:
            print(f"❌ HTTP Error: {resp.status_code}")
            print(f"   Response: {resp.text[:500]}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_stats()
