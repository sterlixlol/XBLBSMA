#!/usr/bin/env python3
"""
Xiaomi Bootloader Unlock API Attacker - "THE SURGEON"
Direct API injection to bypass UI lag and secure an unlock slot.
"""
import time
import json
import requests
import argparse
import threading
from datetime import datetime, timedelta
from pathlib import Path

# ================= CONFIGURATION =================
SCRIPT_DIR = Path(__file__).parent.absolute()
TOKENS_FILE = SCRIPT_DIR / "TOKENS_BACKUP.json"
API_URL = "https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth"

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
    device_id = device.get("deviceId", "")
    version_code = device.get("versionCode", "500429")
    version_name = device.get("versionName", "5.4.29")
    
    return {
        "Host": "sgp-api.buy.mi.com",
        "Cookie": f"new_bbs_serviceToken={token};versionCode={version_code};versionName={version_name};deviceId={device_id};",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/4.12.0"
    }

HEADERS = load_headers()

# Attack Settings
THREADS = 100          # Number of parallel threads
DURATION = 10          # Seconds to spam (Extended burst)
REQUEST_DELAY = 0.001  # Delay between requests per thread (1ms)
TARGET_HOUR = 17       # 5 PM (Local Time)
TARGET_MINUTE = 0
TARGET_SECOND = 0
# =================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color):
    print(f"{color}{text}{Colors.END}")

def send_request(thread_id, stop_event, stats):
    """Worker function to spam the API."""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Toggle 'is_retry' to look slightly organic
    payload = {"is_retry": False}

    while not stop_event.is_set():
        try:
            # Alternating retry flag
            payload["is_retry"] = not payload["is_retry"]
            
            start_req = time.time()
            response = session.post(API_URL, json=payload, timeout=2)
            latency = (time.time() - start_req) * 1000

            stats['total'] += 1
            
            # Log significant responses
            if response.status_code == 200:
                data = response.json()
                code = data.get('code', -1)
                msg = data.get('message', 'No message')
                result_data = data.get('data', {})
                apply_result = result_data.get('apply_result', -1)
                
                # Success Codes
                if code == 0:
                    if apply_result == 3 or apply_result == 6:
                        # Soft Failure (Quota Full / Not Time Yet)
                        stats['quota_full'] += 1
                        if stats['quota_full'] % 10 == 0:
                            print(f"[Thread-{thread_id}] ⏳ Server says: 'Result {apply_result}' (Full/Wait)", end='\r')
                    else:
                        # REAL SUCCESS (Result is likely 1 or something else)
                        print_colored(f"\n🎉 [Thread-{thread_id}] JACKPOT! Result: {apply_result}", Colors.GREEN + Colors.BOLD)
                        print(json.dumps(data, indent=2))
                        stop_event.set() # STOP EVERYTHING WE WON
                        return
                
                # Common Failure Codes
                elif code == 401 or "auth" in msg.lower():
                    stats['auth_fail'] += 1
                    # Token might be expired, but keep trying
                    if stats['auth_fail'] % 10 == 0:
                        print_colored(f"[Thread-{thread_id}] ⚠️ Auth Error: {msg}", Colors.RED)
                
                elif "limit" in msg.lower() or "quota" in msg.lower():
                    stats['quota_full'] += 1
                
                else:
                    # Unknown code, print it
                    print(f"[Thread-{thread_id}] Code: {code} | Result: {apply_result} | Latency: {latency:.0f}ms")
            
            else:
                print_colored(f"[Thread-{thread_id}] HTTP {response.status_code}", Colors.YELLOW)

        except requests.exceptions.RequestException as e:
            stats['errors'] += 1
            # print(f"[Thread-{thread_id}] Error: {e}")
        
        time.sleep(REQUEST_DELAY)

def countdown_and_launch(target_time):
    """Wait for the exact moment (minus buffer)."""
    print_colored(f"🎯 Target Time: {target_time.strftime('%H:%M:%S.%f')}", Colors.CYAN)
    
    # PRE-LAUNCH BUFFER: Start attacking 1.5 seconds early
    launch_time = target_time - timedelta(seconds=1.5)
    print_colored(f"🚀 Launch Time: {launch_time.strftime('%H:%M:%S.%f')} (1.5s buffer)", Colors.YELLOW)
    
    while True:
        now = datetime.now()
        remaining = (launch_time - now).total_seconds()
        
        if remaining <= 0:
            break
        
        if remaining > 10:
            time.sleep(1)
            print(f"Waiting... {int(remaining)}s", end='\r')
        else:
            print(f"🔥 LAUNCH IN {remaining:.3f}s", end='\r')
            time.sleep(0.001)

def main():
    parser = argparse.ArgumentParser(description="Xiaomi API Direct Attacker")
    parser.add_argument('--now', action='store_true', help="Attack IMMEDIATELY (Test Mode)")
    parser.add_argument('--hour', type=int, default=TARGET_HOUR, help="Target Hour (24h format)")
    args = parser.parse_args()

    print_colored("="*60, Colors.RED)
    print_colored(" ⚔️  XIAOMI API SURGEON - DIRECT ATTACK  ⚔️", Colors.RED + Colors.BOLD)
    print_colored("="*60, Colors.RED)
    
    # Schedule
    now = datetime.now()
    if args.now:
        target_time = now + timedelta(seconds=1)
        launch_time = target_time # No buffer for 'now'
    else:
        target_time = now.replace(hour=args.hour, minute=TARGET_MINUTE, second=TARGET_SECOND, microsecond=0)
        if target_time < now:
            # If 5 PM passed, target tomorrow
            target_time += timedelta(days=1)
        
        countdown_and_launch(target_time)

    # LAUNCH
    print_colored(f"\n🚀 STARTING ATTACK WITH {THREADS} THREADS!", Colors.GREEN + Colors.BOLD)
    
    stop_event = threading.Event()
    stats = {'total': 0, 'auth_fail': 0, 'quota_full': 0, 'errors': 0}
    threads = []

    # Start threads
    for i in range(THREADS):
        t = threading.Thread(target=send_request, args=(i, stop_event, stats))
        t.daemon = True
        threads.append(t)
        t.start()

    # Monitor loop
    start_attack = time.time()
    try:
        while time.time() - start_attack < DURATION and not stop_event.is_set():
            time.sleep(0.5)
            elapsed = time.time() - start_attack
            rate = stats['total'] / elapsed
            print(f"Stats: {stats['total']} Reqs | {rate:.1f} Req/s | Quota: {stats['quota_full']} | Auth: {stats['auth_fail']}", end='\r')
            
    except KeyboardInterrupt:
        print_colored("\n🛑 Manual Stop", Colors.YELLOW)
    
    stop_event.set()
    print_colored(f"\n\n🏁 Attack Finished.", Colors.CYAN)
    print_colored(f"Total Requests: {stats['total']}", Colors.CYAN)
    print_colored(f"Quota/Limit Hits: {stats['quota_full']}", Colors.YELLOW)
    
    if stats['auth_fail'] > 0:
        print_colored(f"⚠️ Auth Failures: {stats['auth_fail']} (Token might be expired!)", Colors.RED)

if __name__ == "__main__":
    main()