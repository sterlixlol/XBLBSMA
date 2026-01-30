#!/usr/bin/env python3
"""
Xiaomi Community Ghost Farmer - API EDITION
Farms engagement points directly via API requests.
No ADB, no UI rendering, no screen on.
"""
import time
import json
import random
import requests
import argparse
from datetime import datetime
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

# Comment Templates
COMMENTS = [
    "Nice post!", "Great share!", "Thanks for this info.", 
    "Very helpful.", "Awesome!", "Cool.", "Looks good.", 
    "Interesting read.", "Good one.", "Appreciate it.",
    "Wow!", "Nice capture.", "Amazing.", "Top tier.",
    "Love this.", "Keep it up.", "Useful.", "Fantastic."
]

# Task IDs (Based on your interception)
# 4 = Like Task?, 6 = Comment Task?
TASKS = [4, 6] 

# Post Templates (Title, Content)
POST_TOPICS = [
    ("Good morning everyone!", "Hope everyone has a great day with their Xiaomi devices."),
    ("Photography tips?", "Does anyone have good settings for night mode on the 13T?"),
    ("Battery life", "How is everyone's battery holding up on HyperOS?"),
    ("Wallpaper share", "Looking for some cool minimal wallpapers."),
    ("Update question", "Just updated my phone, feels smoother!"),
    ("Feature request", "I wish we had more lock screen customization."),
    ("Hello Community", "Glad to be here!"),
    ("HyperOS is great", "Really liking the new animations."),
    ("Shot on Xiaomi", "Loving the camera quality."),
    ("Question", "What is your favorite Xiaomi phone of all time?")
]

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

class GhostFarmer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        # Daily Caps (approximate based on research)
        self.limits = {
            'likes': 5, 
            'comments': 5, 
            'shares': 3, 
            'posts': 5
        }
        self.stats = {'likes': 0, 'comments': 0, 'shares': 0, 'posts': 0, 'tasks': 0, 'errors': 0}

    def fetch_feed(self):
        """Fetches the latest feed to find valid Post IDs (aid). Rotates endpoints."""
        endpoints = [
            f"{BASE_URL}/thread/appHome/hot-board",
            f"{BASE_URL}/thread/appHome/index?limit=20",
            f"{BASE_URL}/thread/appHome/recommend-sort"
        ]
        
        for url in endpoints:
            try:
                endpoint_name = url.split('/')[-1].split('?')[0]
                print_colored(f"📡 Fetching feed ({endpoint_name})...", Colors.CYAN)
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0:
                        # Handle different data structures
                        # 1. Direct list: data -> []
                        # 2. Wrapped list: data -> data -> []
                        # 3. Records: data -> data -> records -> []
                        
                        raw_items = data.get('data')
                        items = []
                        
                        if isinstance(raw_items, list):
                            items = raw_items
                        elif isinstance(raw_items, dict):
                            items = raw_items.get('list') or raw_items.get('records') or []
                        
                        post_ids = []
                        for item in items:
                            # Try to find the ID field
                            pid = item.get('id') or item.get('thread_id') or item.get('aid')
                            if pid:
                                post_ids.append(pid)
                        
                        if post_ids:
                            print_colored(f"✅ Found {len(post_ids)} posts.", Colors.GREEN)
                            return post_ids
            except Exception as e:
                # print(f"   ⚠️ Endpoint failed: {e}")
                pass
        
        print_colored("❌ All feeds failed. Using fallback.", Colors.RED)
        return [1869950, 1869951, 1869952, 1869949]

    def like_post(self, aid):
        if self.stats['likes'] >= self.limits['likes']: return False
        
        url = f"{BASE_URL}/action/like"
        payload = {"aid": int(aid), "action": True}
        try:
            time.sleep(random.uniform(1, 3))
            resp = self.session.post(url, json=payload)
            if resp.status_code == 200:
                print_colored(f"   ❤️ Liked post {aid}", Colors.GREEN)
                self.stats['likes'] += 1
                return True
        except: pass
        return False

    def comment_post(self, aid):
        if self.stats['comments'] >= self.limits['comments']: return False

        url = f"{BASE_URL}/comment/add"
        text = random.choice(COMMENTS)
        payload = {"text": text, "aid": int(aid)}
        try:
            time.sleep(random.uniform(2, 5))
            resp = self.session.post(url, json=payload)
            if resp.status_code == 200:
                print_colored(f"   💬 Commented: '{text}' on {aid}", Colors.BLUE)
                self.stats['comments'] += 1
                return True
        except: pass
        return False

    def share_post(self, aid):
        """Sends a SHARE action (simulated)."""
        if self.stats['shares'] >= self.limits['shares']: return False

        # Sharing usually triggers a task/finish or a specific share endpoint
        # Based on logs, we can try the 'task/finish' with a share task ID (guessing 1 or 2?)
        # Or usually just requesting the 'share' URL counts.
        # For now, let's try a generic share endpoint pattern or just task finish
        
        # NOTE: Without a specific 'share' endpoint capture, we assume it's a client-side action 
        # that triggers a task/finish report. Let's try Task ID 1 (often daily checkin/share).
        
        # Let's try to 'browse' the share link
        url = f"{BASE_URL}/thread/share?aid={aid}"
        try:
            self.session.get(url) # Fake the share request
            print_colored(f"   🔄 Shared post {aid}", Colors.YELLOW)
            self.stats['shares'] += 1
            self.finish_task(1) # Guessing Task 1 is share/checkin
            return True
        except: pass
        return False

    def create_post(self):
        """Creates a new text thread."""
        if self.stats['posts'] >= self.limits['posts']: return False

        url = f"{BASE_URL}/thread/publish" # Standard pattern, might need verification
        title, content = random.choice(POST_TOPICS)
        
        # This payload is a guess based on standard Xiaomi API structure.
        # We might need to capture a real post creation to be 100% sure.
        payload = {
            "subject": title,
            "message": content,
            "fid": 100, # Forum ID (100 is often General/Chat)
            "type_id": 0
        }
        
        try:
            print_colored(f"   📝 Creating post: {title}...", Colors.CYAN)
            time.sleep(random.uniform(3, 6))
            resp = self.session.post(url, json=payload)
            if resp.status_code == 200 and resp.json().get('code') == 0:
                print_colored(f"   ✅ Post created!", Colors.GREEN + Colors.BOLD)
                self.stats['posts'] += 1
                return True
            else:
                # If fail, might be due to missing Forum ID or strict structure
                print_colored(f"   ⚠️ Post failed: {resp.text[:100]}", Colors.RED)
        except: pass
        return False

    def finish_task(self, task_id):
        """Tells the server we finished a task."""
        url = f"{BASE_URL}/task/finish"
        payload = {"task_id": task_id}
        try:
            time.sleep(0.5)
            self.session.post(url, json=payload)
        except: pass

    def run(self, hours):
        print_colored(f"👻 Ghost Farmer active for {hours} hours.", Colors.GREEN + Colors.BOLD)
        print_colored(f"🎯 Targets: {self.limits}", Colors.CYAN)
        
        end_time = time.time() + (hours * 3600)
        
        while time.time() < end_time:
            # Check if we hit all limits
            if all(self.stats[k] >= self.limits[k] for k in self.limits):
                print_colored("\n🎉 Daily Caps Reached! Sleeping for 12 hours...", Colors.GREEN)
                time.sleep(12 * 3600)
                # Reset stats for next day
                for k in self.stats: self.stats[k] = 0
                continue

            # 1. Get Posts
            posts = self.fetch_feed()
            if not posts:
                time.sleep(60)
                continue

            # 2. Interact
            for aid in posts:
                if time.time() > end_time: break
                
                # Decision Matrix
                # Prioritize high value tasks that aren't maxed
                
                # 1. Create Post (High Priority)
                if self.stats['posts'] < self.limits['posts'] and random.random() < 0.3:
                    self.create_post()
                
                # 2. Share (Medium)
                elif self.stats['shares'] < self.limits['shares'] and random.random() < 0.4:
                    self.share_post(aid)

                # 3. Comment (Medium)
                elif self.stats['comments'] < self.limits['comments'] and random.random() < 0.5:
                    if self.comment_post(aid):
                        self.finish_task(6)

                # 4. Like (Low)
                elif self.stats['likes'] < self.limits['likes']:
                    if self.like_post(aid):
                        self.finish_task(4)
                
                else:
                    print(f"   ⏩ Limits met, skipping interaction.")

                # Delay
                delay = random.uniform(5, 15)
                time.sleep(delay)
            
            print("\n   🔄 Batch complete. Refreshing feed...")
            time.sleep(30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=48)
    args = parser.parse_args()
    
    farmer = GhostFarmer()
    try:
        farmer.run(args.hours)
    except KeyboardInterrupt:
        print_colored("\n🛑 Farmer stopped.", Colors.RED)
        print(f"Final Stats: {farmer.stats}")
