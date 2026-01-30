#!/usr/bin/env python3
"""
Xiaomi Community Engagement Farming Bot - GOD MODE (UI AUTOMATOR)
Automates likes, comments, views, and scrolls using ADB UI Dumps for perfect accuracy.
"""
import os
import sys
import time
import argparse
import subprocess
import random
import json
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta

# Check for dependencies and provide helpful errors
try:
    from PIL import Image, ImageGrab, ImageDraw, ImageStat
except ImportError:
    print("Pillow library not found! Please install it:")
    print("pip install Pillow")
    sys.exit(1)

try:
    import tkinter as tk
except ImportError:
    print("tkinter not found! This is required for calibration.")
    print("On Debian/Ubuntu: sudo apt-get install python3-tk")
    print("On Fedora/RHEL: sudo dnf install python3-tkinter")
    sys.exit(1)


# ================= CONFIGURATION =================
ADB_PATH = os.path.expanduser("~/Downloads/platform-tools/adb")
PACKAGE_NAME = "com.mi.global.bbs"
SCREEN_RESOLUTION = {}  # Will be auto-detected
TEMPLATE_DIR = "templates"
CONFIG_FILE = "bot_config.json"
SCREENSHOT_PATH = os.path.join(os.getcwd(), "engagement_screen.png")

# Action Delays (in seconds)
MIN_ACTION_DELAY = 2
MAX_ACTION_DELAY = 8

# Scroll settings
SCROLL_DURATION_MIN = 200  # ms
SCROLL_DURATION_MAX = 600  # ms

# Comment settings
COMMENT_TEMPLATES = [
    "Nice post!", "Great share!", "Thanks for this.", "Very helpful.",
    "Awesome!", "Cool.", "Looks good.", "Interesting.", "Good one."
]
# ADB 'input text' often crashes with Unicode emojis. Using ASCII safe alternatives.
EMOJI_OPTIONS = [":)", ":D", "<3", ";)", "!!", "^^", "Wow!", "Nice"]

# Session settings
SESSION_DURATION_HOURS = 48
TEST_DURATION_MINUTES = 5
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

class ConfigManager:
    """Manages saving and loading of bot configuration (coordinates)."""
    @staticmethod
    def load_config():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print_colored("⚠️  Config file corrupted. Starting fresh.", Colors.YELLOW)
                return {}
        return {}

    @staticmethod
    def save_config(config):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print_colored(f"✅ Configuration saved to {CONFIG_FILE}", Colors.GREEN)

def run_adb_command(command, capture=False, silent=False):
    """Run ADB command with error handling"""
    full_cmd = f"sudo {ADB_PATH} {command}"
    try:
        if capture:
            result = subprocess.run(full_cmd, shell=True, check=True,
                                  capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        else:
            subprocess.run(full_cmd, shell=True, check=True,
                         stdout=subprocess.DEVNULL if silent else None,
                         stderr=subprocess.DEVNULL if silent else None,
                         timeout=10)
            return None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        if not silent:
            print_colored(f"⚠️ ADB command failed: {full_cmd}", Colors.RED)
        return "ERROR"

def capture_screenshot():
    """Capture a screenshot from the device and pull it locally."""
    run_adb_command(f"shell screencap -p /sdcard/screen.png", silent=True)
    if run_adb_command(f"pull /sdcard/screen.png {SCREENSHOT_PATH}", silent=True) != "ERROR":
        # Fix permissions: change owner of the file from root (adb) to current user
        try:
            user = os.environ.get('USER', 'sterlix') # Fallback to sterlix if env var missing
            subprocess.run(f"sudo chown {user}:{user} {SCREENSHOT_PATH}", shell=True, check=False)
        except Exception:
            pass # Best effort

        if os.path.exists(SCREENSHOT_PATH):
            return Image.open(SCREENSHOT_PATH)
    print_colored("❌ Failed to capture or pull screenshot.", Colors.RED)
    return None

def get_screen_resolution():
    """Auto-detect screen resolution from a screenshot"""
    global SCREEN_RESOLUTION
    print_colored("📱 Detecting screen resolution...", Colors.CYAN)
    screen = capture_screenshot()
    if screen:
        width, height = screen.size
        SCREEN_RESOLUTION = {'width': width, 'height': height}
        print_colored(f"✅ Resolution detected: {width}x{height}", Colors.GREEN)
        return True
    else:
        print_colored("❌ Could not get screen resolution.", Colors.RED)
        return False

def tap(x, y, randomize=True):
    """Simulate a tap at a given coordinate, with optional randomization."""
    tap_x = int(x + random.randint(-5, 5)) if randomize else int(x)
    tap_y = int(y + random.randint(-5, 5)) if randomize else int(y)
    print(f"   ➡️ Tapping at ({tap_x}, {tap_y})")
    run_adb_command(f"shell input tap {tap_x} {tap_y}")

def swipe(start_x, start_y, end_x, end_y, duration):
    """Simulate a swipe."""
    print(f"   ➡️ Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y})")
    run_adb_command(f"shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}")

def type_text(text):
    """Type a string of text, escaping characters as needed for ADB."""
    print(f'   ➡️ Typing: "{text}"')
    # Escape special shell characters: space, quote, parentheses, etc.
    escaped_text = text.replace(" ", "%s").replace("'", "''").replace("(", "\\(").replace(")", "\\)")
    run_adb_command(f"shell input text '{escaped_text}'")

def human_like_delay(short=False):
    """Wait for a random, human-like duration. Occasionally takes a 'break'."""
    if short:
        delay = random.uniform(0.5, 1.5)
    else:
        # 5% chance of a "distraction" pause (10-30 seconds)
        if random.random() < 0.05:
            distraction = random.uniform(10, 30)
            print_colored(f"   😴 Taking a short break ({int(distraction)}s)...", Colors.BLUE)
            time.sleep(distraction)
            return
        
        delay = random.uniform(MIN_ACTION_DELAY, MAX_ACTION_DELAY)
    
    time.sleep(delay)

def human_like_scroll():
    """Perform a randomized, human-like scroll down the screen."""
    width = SCREEN_RESOLUTION['width']
    height = SCREEN_RESOLUTION['height']

    # Randomize start/end points to look less robotic
    start_x = random.randint(int(width * 0.45), int(width * 0.55))
    start_y = random.randint(int(height * 0.6), int(height * 0.8))
    
    # Slight horizontal drift is human
    end_x = start_x + random.randint(-int(width*0.02), int(width*0.02))
    end_y = random.randint(int(height * 0.2), int(height * 0.4))
    
    duration = random.randint(SCROLL_DURATION_MIN, SCROLL_DURATION_MAX)
    swipe(start_x, start_y, end_x, end_y, duration)

def open_app():
    """Start the Xiaomi Community app."""
    print_colored("📱 Opening Xiaomi Community app...", Colors.CYAN)
    run_adb_command(f"shell monkey -p {PACKAGE_NAME} -c android.intent.category.LAUNCHER 1")
    time.sleep(5)

def close_app():
    """Force-stop the Xiaomi Community app."""
    print_colored("🛑 Closing Xiaomi Community app...", Colors.YELLOW)
    run_adb_command(f"shell am force-stop {PACKAGE_NAME}")
    time.sleep(1)

class UINavigator:
    """Uses ADB UIAutomator to find reliable tap targets from the XML layout."""
    
    @staticmethod
    def get_clickable_elements():
        """
        Dumps the UI hierarchy to XML and parses it for content.
        Returns a list of (x, y) coordinates for likely posts.
        """
        # 1. Dump UI
        run_adb_command("shell uiautomator dump /sdcard/window_dump.xml", silent=True)
        
        # 2. Pull XML and fix permissions
        local_xml = os.path.join(os.getcwd(), "window_dump.xml")
        if run_adb_command(f"pull /sdcard/window_dump.xml {local_xml}", silent=True) == "ERROR":
             return []
        
        # Fix permissions: change owner from root to current user
        try:
            user = os.environ.get('USER', 'sterlix')
            subprocess.run(f"sudo chown {user}:{user} {local_xml}", shell=True, check=False, capture_output=True)
        except Exception:
            pass  # Best effort

        # 3. Parse XML
        targets = []
        try:
            tree = ET.parse(local_xml)
            root = tree.getroot()
            
            # Known non-post text to ignore
            IGNORE_TEXT = ["Search", "Following", "Headline", "Discover", "Photo Wall", "Ask", "OS", "Activity", "Wallpaper", "Follow", "HOME", "FORUM", "ME"]

            for node in root.iter('node'):
                resource_id = node.attrib.get('resource-id', '')
                text = node.attrib.get('text', '')
                bounds = node.attrib.get('bounds')
                pkg = node.attrib.get('package', '')
                
                # Must be the Xiaomi App
                if "com.mi.global.bbs" not in pkg:
                    continue

                # Criteria 1: It has significant text (Post Title/Body) -> BEST TARGET
                is_text_content = len(text) > 20 and text not in IGNORE_TEXT
                
                # Criteria 2: Explicitly a Recycler Item (Container) -> GOOD TARGET
                # But careful not to click the 'Like' or 'Share' button inside it
                is_container = "item" in resource_id or "card" in resource_id or "container" in resource_id
                
                # Criteria 3: STRICTLY AVOID IMAGES
                # Tapping images often opens lightbox, not post.
                is_image = "image" in resource_id or "cover" in resource_id or "img" in resource_id or "pic" in resource_id

                if (is_text_content or is_container) and not is_image:
                    try:
                        matches = re.findall(r'\[(\d+),(\d+)\]', bounds)
                        if len(matches) == 2:
                            x1, y1 = int(matches[0][0]), int(matches[0][1])
                            x2, y2 = int(matches[1][0]), int(matches[1][1])
                            
                            width = x2 - x1
                            height = y2 - y1
                            
                            # Filter out tiny icons, but allow smaller text blocks
                            # Width must be substantial to be a post body/title
                            if width > 200 and height > 50: 
                                center_x = int((x1 + x2) / 2)
                                center_y = int((y1 + y2) / 2)
                                targets.append((center_x, center_y))
                    except:
                        pass
                        
        except Exception as e:
            print_colored(f"XML Parse Error: {e}", Colors.RED)
            
        return targets

    @staticmethod
    def find_and_tap_post(fallback_coords=None):
        """Dumps UI, finds big clickable cards, and taps one."""
        print_colored("   🧠 Analyzing UI Structure...", Colors.CYAN)
        targets = UINavigator.get_clickable_elements()
        
        if targets:
            # Pick a target from the middle of the list (usually the most visible post)
            # Avoid the very first one (might be a header)
            if len(targets) > 1:
                target = targets[1] # Second item is usually the best bet
            else:
                target = targets[0]

            print_colored(f"   🎯 Found UI Element at ({target[0]}, {target[1]})", Colors.GREEN)
            tap(target[0], target[1])
            return True
        else:
            print_colored("   ⚠️ No clickable posts found in UI dump. Scrolling...", Colors.YELLOW)
            human_like_scroll()
            return False

class Calibrator:
    """GUI tool to define tap targets."""
    def __init__(self, master, screenshot_path, key, instruction):
        self.master = master
        self.screenshot = Image.open(screenshot_path)
        self.key = key
        self.instruction = instruction
        self.coords = None
        self.rect = None
        self.start_x = None
        self.start_y = None

        self.master.title(f"Calibrate: {key}")
        
        # Add instruction label
        self.label = tk.Label(master, text=f"DRAW A BOX around {instruction}", bg="yellow", font=("Arial", 12))
        self.label.pack(fill=tk.X)

        self.canvas = tk.Canvas(master, width=self.screenshot.width, height=self.screenshot.height)
        self.canvas.pack()

        self.tk_image = tk.PhotoImage(file=screenshot_path)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline='red', width=2)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        # Calculate center point
        center_x = int((self.start_x + end_x) / 2)
        center_y = int((self.start_y + end_y) / 2)
        
        self.coords = (center_x, center_y)
        print_colored(f"✅ Captured coordinate for '{self.key}': {self.coords}", Colors.GREEN)
        self.master.quit()

def run_calibrate_mode():
    """Guide the user to calibrate key UI elements via a GUI."""
    print_colored("=" * 60, Colors.CYAN)
    print_colored("🛠️  VISUAL CALIBRATION MODE 🛠️", Colors.CYAN + Colors.BOLD)
    print_colored("=" * 60, Colors.CYAN)
    print("We will define tap targets for the bot. For each step:")
    print("1. Navigate the phone to the requested screen.")
    print("2. Press Enter here.")
    print("3. Draw a box around the requested button/area in the popup window.")

    config = ConfigManager.load_config()
    
    # Calibration steps: (Key, Description, Pre-condition hint)
    steps = [
        # "feed_post" is no longer needed as UINavigator finds posts automatically via XML
        ("detail_like", "the LIKE button", "Open any post to see the DETAIL VIEW."),
        ("detail_comment_btn", "the COMMENT button (to open input)", "Stay on the DETAIL VIEW."),
        ("input_field", "the TEXT INPUT field", "Tap the comment button to open the KEYBOARD/INPUT."),
        ("submit_btn", "the SEND/SUBMIT button", "Type a test letter if needed to see the send button."),
        ("back_btn", "the BACK button (usually top left)", "Go to any post or screen with a back arrow.")
    ]

    for key, desc, hint in steps:
        print(f"\n👉 STEP: Calibrate {key}")
        print(f"   Hint: {hint}")
        input(f"   Press Enter when ready...")
        
        print_colored(f"   Capturing screen...", Colors.YELLOW)
        screenshot = capture_screenshot()
        if not screenshot:
            print_colored("   Skipping...", Colors.RED)
            continue
        
        screenshot.save(SCREENSHOT_PATH)

        root = tk.Tk()
        # Force window to top
        root.attributes('-topmost', True)
        app = Calibrator(root, SCREENSHOT_PATH, key, desc)
        root.mainloop()
        
        if app.coords:
            config[key] = app.coords
        
        root.destroy()
    
    ConfigManager.save_config(config)
    print_colored("\n✅ Calibration complete! Ready to farm.", Colors.GREEN)


def run_engagement_loop(duration_minutes):
    """Main loop for performing engagement actions."""
    config = ConfigManager.load_config()
    # Note: 'feed_post' calibration is now optional/fallback thanks to UINavigator
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    print_colored(f"🚀 Starting engagement farming for {duration_minutes} minutes.", Colors.GREEN)
    
    stats = {'scrolls': 0, 'likes': 0, 'comments': 0, 'views': 0, 'restarts': 0, 'errors': 0}
    
    open_app()

    while datetime.now() < end_time:
        print_colored("-" * 40, Colors.BLUE)
        
        # Weighted random actions
        action = random.choices(['scroll', 'view'], weights=[0.5, 0.5], k=1)[0] # Increased view chance since we are smarter now

        try:
            if action == 'scroll':
                print("Action: Scroll feed")
                human_like_scroll()
                stats['scrolls'] += 1

            elif action == 'view':
                print("Action: View Post")
                
                # USE UI NAVIGATOR (GOD MODE)
                success = UINavigator.find_and_tap_post()
                
                if success:
                    stats['views'] += 1
                    human_like_delay() # Wait for load

                    # Inside the post
                    # Decide: Like? Comment? Just read?
                    # Aggressive farming: Mostly Like (50%), often Comment (30%), rarely just read (20%)
                    post_action = random.choices(
                        ['read', 'like', 'comment'], 
                        weights=[0.2, 0.5, 0.3], 
                        k=1
                    )[0]

                    if post_action == 'like' and 'detail_like' in config:
                        print("   Sub-action: Like post")
                        tap(*config['detail_like'])
                        stats['likes'] += 1
                    
                    elif post_action == 'comment' and 'detail_comment_btn' in config:
                        print("   Sub-action: Comment")
                        tap(*config['detail_comment_btn'])
                        human_like_delay(short=True)
                        
                        if 'input_field' in config:
                            tap(*config['input_field'])
                            
                            # Use ASCII safe emoticons
                            comment_text = random.choice(COMMENT_TEMPLATES) + " " + random.choice(EMOJI_OPTIONS)
                            type_text(comment_text)
                            human_like_delay(short=True)
                            
                            if 'submit_btn' in config:
                                tap(*config['submit_btn'])
                                stats['comments'] += 1
                                human_like_delay()
                    
                    elif post_action == 'read':
                        print("   Sub-action: Just reading")
                        human_like_scroll()
                        human_like_delay()

                    # Go back to feed
                    print("   Going back to feed...")
                    
                    # Double-tap strategy: Tap visual button AND fire hardware key
                    if 'back_btn' in config:
                        tap(*config['back_btn'])
                    
                    # Fire hardware back key immediately as insurance
                    run_adb_command("shell input keyevent 4")
                        
                    human_like_delay(short=True) # Wait for feed to reappear
                else:
                    pass

            print_colored(f"Stats: {stats}", Colors.YELLOW)
            human_like_delay()

        except Exception as e:
            print_colored(f"An error occurred: {e}", Colors.RED)
            stats['errors'] += 1
            if stats['errors'] % 5 == 0:
                print_colored("Too many errors, restarting app...", Colors.YELLOW)
                close_app()
                time.sleep(2)
                open_app()
                stats['restarts'] += 1

    close_app()
    print_colored("=" * 60, Colors.GREEN)
    print_colored("✅ Engagement farming session complete!", Colors.GREEN)
    print_colored(f"Final Stats: {stats}", Colors.GREEN)
    print_colored("=" * 60, Colors.GREEN)


def main():
    parser = argparse.ArgumentParser(
        description="Xiaomi Community Engagement Farming Bot - Vision Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--calibrate", action="store_true", help="Run interactive visual calibration mode.")
    parser.add_argument("--test", action="store_true", help=f"Run a short {TEST_DURATION_MINUTES}-minute test session.")
    parser.add_argument("--hours", type=int, default=SESSION_DURATION_HOURS, help=f"Duration for the farming session in hours (default: {SESSION_DURATION_HOURS}).")

    args = parser.parse_args()

    if not get_screen_resolution():
        sys.exit(1)

    if args.calibrate:
        run_calibrate_mode()
    elif args.test:
        run_engagement_loop(duration_minutes=TEST_DURATION_MINUTES)
    else:
        run_engagement_loop(duration_minutes=args.hours * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # print_colored might not be defined if error occurs during import, 
        # but here we are safe as it is defined above.
        print_colored("\n\n⚠️ Interrupted by user. Closing app...", Colors.YELLOW)
        close_app()
        sys.exit(0)
    except Exception as e:
        # Fallback if Colors/print_colored not defined yet
        try:
            print_colored(f"\n\n❌ A fatal error occurred: {e}", Colors.RED)
        except NameError:
             print(f"\n\n❌ A fatal error occurred: {e}")
        close_app()
        sys.exit(1)
