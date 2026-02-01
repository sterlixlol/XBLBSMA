#!/usr/bin/env python3
"""
Xiaomi Bootloader Unlock API Attacker - "THE SURGEON"
Direct API injection to bypass UI lag and secure an unlock slot.
"""
import os
import time
import json
import random
import requests
import argparse
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path

# ================= CONFIGURATION =================
SCRIPT_DIR = Path(__file__).parent.parent.absolute()  # Go to repo root
TOKENS_FILE = SCRIPT_DIR / "TOKENS_BACKUP.json"
API_URL = "https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth"

# Setup logging
log_file = SCRIPT_DIR / "attack.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
REQUEST_DELAY = 0.001  # Base delay between requests per thread (1ms)
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

def send_notification(title: str, message: str, icon: str = "dialog-information"):
    """Send desktop notification using notify-send (Linux) or osascript (macOS)."""
    try:
        if os.name == 'posix':
            # Try notify-send first (Linux)
            result = os.system(f'notify-send "{title}" "{message}" --icon={icon} 2>/dev/null')
            if result != 0:
                # Fallback to osascript (macOS)
                os.system(f'osascript -e \'display notification "{message}" with title "{title}"\' 2>/dev/null')
    except:
        pass

def save_unlock_ticket(winner_data: dict, stats: dict, elapsed: float):
    """Save unlock ticket to file for safekeeping."""
    ticket_file = SCRIPT_DIR / "unlock_ticket.json"
    
    ticket = {
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "total_requests": stats['total'],
        "deadline_timestamp": winner_data.get('data', {}).get('deadline'),
        "deadline_formatted": winner_data.get('data', {}).get('deadline_format'),
        "raw_response": winner_data
    }
    
    try:
        with open(ticket_file, 'w') as f:
            json.dump(ticket, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save ticket: {e}")
        return False

def health_check():
    """Quick health check before attack."""
    if HEADERS is None:
        print_colored("❌ Cannot start attack - tokens not configured!", Colors.RED)
        return False
    
    print_colored("🔍 Running health check...", Colors.CYAN)
    
    try:
        url = "https://sgp-api.buy.mi.com/bbs/api/global/user/data"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                user = data.get('data', {})
                username = user.get('user_name', 'Unknown')
                print_colored(f"✓ Token valid - User: {username}", Colors.GREEN)
                return True
            elif data.get('code') == 100004:
                print_colored("❌ Token expired! Re-extract via mitmproxy.", Colors.RED)
                return False
        elif resp.status_code == 401:
            print_colored("❌ Authentication failed - Token expired!", Colors.RED)
            return False
            
    except Exception as e:
        print_colored(f"⚠ Health check failed: {e} - will proceed anyway", Colors.YELLOW)
        
    return True

def send_request(thread_id, stop_event, stats):
    """Worker function to spam the API."""
    if HEADERS is None:
        print_colored("❌ Cannot start attack - tokens not configured!", Colors.RED)
        stop_event.set()
        return
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Toggle 'is_retry' to look slightly organic
    payload = {"is_retry": False}
    
    # Random initial delay to stagger thread starts
    time.sleep(random.uniform(0, 0.1))

    while not stop_event.is_set():
        try:
            # Alternating retry flag
            payload["is_retry"] = not payload["is_retry"]
            
            start_req = time.time()
            response = session.post(API_URL, json=payload, timeout=2)
            latency = (time.time() - start_req) * 1000

            stats['total'] += 1
            
            # Handle rate limiting
            if response.status_code == 429:
                stats['rate_limited'] += 1
                stats['errors'] += 1
                # Exponential backoff
                time.sleep(random.uniform(0.5, 2.0))
                continue
            
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
                        
                        # Save the winning data
                        stats['winner'] = {'thread': thread_id, 'data': data}
                        logger.info(f"SUCCESS! Thread-{thread_id} acquired unlock ticket")
                        
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
        except Exception as e:
            stats['errors'] += 1
            logger.error(f"Thread-{thread_id} error: {e}")
        
        # Jitter: random delay between 0.5ms and 3ms
        time.sleep(random.uniform(0.0005, 0.003))

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
    
    # Health check
    if not health_check():
        return
    
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
    logger.info(f"Attack starting - Target hour: {args.hour}, Threads: {THREADS}")
    
    stop_event = threading.Event()
    stats = {'total': 0, 'auth_fail': 0, 'quota_full': 0, 'errors': 0, 'rate_limited': 0, 'winner': None}
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
            rate = stats['total'] / elapsed if elapsed > 0 else 0
            status_line = f"Stats: {stats['total']} Reqs | {rate:.1f} Req/s | Quota: {stats['quota_full']} | Auth: {stats['auth_fail']}"
            if stats['rate_limited'] > 0:
                status_line += f" | 429s: {stats['rate_limited']}"
            print(status_line, end='\r')
            
    except KeyboardInterrupt:
        print_colored("\n🛑 Manual Stop", Colors.YELLOW)
        logger.info("Attack manually stopped")
    
    stop_event.set()
    elapsed = time.time() - start_attack
    
    print_colored(f"\n\n🏁 Attack Finished.", Colors.CYAN)
    print_colored(f"Total Requests: {stats['total']}", Colors.CYAN)
    print_colored(f"Quota/Limit Hits: {stats['quota_full']}", Colors.YELLOW)
    
    if stats['rate_limited'] > 0:
        print_colored(f"Rate Limited (429): {stats['rate_limited']}", Colors.YELLOW)
    
    if stats['auth_fail'] > 0:
        print_colored(f"⚠️ Auth Failures: {stats['auth_fail']} (Token might be expired!)", Colors.RED)
    
    # Handle success
    if stats.get('winner'):
        winner_data = stats['winner']['data']
        deadline = winner_data.get('data', {}).get('deadline_format', 'Unknown')
        
        # Save ticket
        saved = save_unlock_ticket(winner_data, stats, elapsed)
        
        # Send notification
        send_notification(
            "XBLBSMA - Unlock Acquired! 🔓",
            f"Bootloader unlock ticket acquired! Deadline: {deadline}",
            "lock-open"
        )
        
        logger.info(f"Unlock ticket saved. Deadline: {deadline}")
        
        print_colored(f"\n✅ Ticket saved to unlock_ticket.json", Colors.GREEN)
        print_colored(f"📅 Unlock Deadline: {deadline}", Colors.GREEN + Colors.BOLD)
    else:
        logger.info(f"Attack completed without success. Total requests: {stats['total']}")

if __name__ == "__main__":
    main()
