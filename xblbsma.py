#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║   XBLBSMA - Xiaomi BootLoader BullShit My Ass                                 ║
║   Premium Terminal Interface                                                   ║
║   "Engineering spite into bootloader freedom since 2026"                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

__version__ = "1.0.0"
__author__ = "sterlix"

import os
import sys
import json
import time
import threading
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Helper for reliable screen clear
def clear_screen():
    """Clear terminal using system command (more reliable than Rich)."""
    os.system('clear' if os.name != 'nt' else 'cls')

# Rich imports
try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich.live import Live
    from rich.layout import Layout
    from rich.style import Style
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("❌ Rich library required: pip install rich")
    sys.exit(1)

# Color palette

class XiaomiTheme:
    """Xiaomi-inspired color palette."""
    # Primary accent
    ORANGE = "#FF6900"
    ORANGE_DIM = "#CC5500"
    ORANGE_GLOW = "#FF8533"
    
    # Gradient colors for logo
    GRAD_RED = "#E53935"
    GRAD_ORANGE = "#FF6900" 
    GRAD_GREEN = "#43A047"
    
    # Backgrounds
    BG_DEEP = "#1A1A1A"
    BG_CARD = "#252525"
    BG_CARD_ACTIVE = "#2D2D2D"
    
    # Text
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#888888"
    TEXT_DIM = "#555555"
    
    # Status
    SUCCESS = "#4CAF50"
    WARNING = "#FFC107"
    ERROR = "#F44336"
    
    # Box drawing
    BORDER = "#444444"
    BORDER_ACTIVE = "#FF6900"

theme = XiaomiTheme()

# Box styles

# Use built-in Rich box styles (custom Box requires exactly 4 chars per line)
XIAOMI_BOX = box.SQUARE
THIN_BOX = box.ROUNDED

# Config

SCRIPT_DIR = Path(__file__).parent.absolute()
TOKENS_FILE = SCRIPT_DIR / "TOKENS_BACKUP.json"

class Config:
    """Configuration manager."""
    def __init__(self):
        self.tokens = {}
        self.device = {}
        self._load()
    
    def _load(self):
        if TOKENS_FILE.exists():
            with open(TOKENS_FILE) as f:
                data = json.load(f)
                self.tokens = data.get("authentication", {})
                self.device = data.get("device", {})
    
    def get_headers(self):
        token = self.tokens.get("new_bbs_serviceToken", "")
        csrf = self.tokens.get("x-csrf-token", "")
        # Check device section first (preferred), fallback to authentication for legacy configs
        device_id = self.device.get("deviceId", "") or self.tokens.get("deviceId", "")
        version_code = self.device.get("versionCode", "500429")
        version_name = self.device.get("versionName", "5.4.29")
        
        headers = {
            "Host": "sgp-api.buy.mi.com",
            "Cookie": f"new_bbs_serviceToken={token};versionCode={version_code};versionName={version_name};deviceId={device_id};",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "okhttp/4.12.0"
        }
        if csrf:
            headers["x-csrf-token"] = csrf
        return headers
    
    def is_configured(self):
        return bool(self.tokens.get("new_bbs_serviceToken"))

config = Config()

# Logo

def get_gradient_logo():
    """Generate the XBLBSMA logo with red→orange→green gradient."""
    
    # Logo lines - each character will be colored based on position
    logo_lines = [
        "██╗  ██╗██████╗ ██╗     ██████╗ ███████╗███╗   ███╗ █████╗ ",
        "╚██╗██╔╝██╔══██╗██║     ██╔══██╗██╔════╝████╗ ████║██╔══██╗",
        " ╚███╔╝ ██████╔╝██║     ██████╔╝███████╗██╔████╔██║███████║",
        " ██╔██╗ ██╔══██╗██║     ██╔══██╗╚════██║██║╚██╔╝██║██╔══██║",
        "██╔╝ ██╗██████╔╝███████╗██████╔╝███████║██║ ╚═╝ ██║██║  ██║",
        "╚═╝  ╚═╝╚═════╝ ╚══════╝╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝",
    ]
    
    # Create gradient from red -> orange -> green
    gradient_colors = [
        "#E53935", "#E8432F", "#EB4D29", "#EE5723", "#F1611D",  # Red to orange
        "#F46B17", "#F77511", "#FA7F0B", "#FD8905", "#FF6900",  # Orange
        "#F27306", "#E57D0C", "#D88712", "#CB9118", "#BE9B1E",  # Orange to yellow-green
        "#B1A524", "#A4AF2A", "#97B930", "#8AC336", "#7DCD3C",  # Yellow-green
        "#70D742", "#63E148", "#56EB4E", "#49F554", "#43A047",  # Green
    ]
    
    result = Text()
    
    for line in logo_lines:
        line_text = Text()
        width = len(line)
        
        for i, char in enumerate(line):
            # Calculate gradient position (0-1)
            pos = i / width
            # Map to color index
            color_idx = int(pos * (len(gradient_colors) - 1))
            color = gradient_colors[color_idx]
            line_text.append(char, style=f"bold {color}")
        
        line_text.append("\n")
        result.append(line_text)
    
    return result

def get_tagline():
    """Get the tagline with styling."""
    tagline = Text()
    tagline.append("X", style=f"bold {theme.ORANGE}")
    tagline.append("iaomi ", style=f"bold {theme.TEXT_SECONDARY}")
    tagline.append("B", style=f"bold {theme.ORANGE}")
    tagline.append("ootLoader ", style=f"bold {theme.TEXT_SECONDARY}")
    tagline.append("B", style=f"bold {theme.ORANGE}")
    tagline.append("ull", style=f"bold {theme.TEXT_SECONDARY}")
    tagline.append("S", style=f"bold {theme.ORANGE}")
    tagline.append("hit ", style=f"bold {theme.TEXT_SECONDARY}")
    tagline.append("M", style=f"bold {theme.ORANGE}")
    tagline.append("y ", style=f"bold {theme.TEXT_SECONDARY}")
    tagline.append("A", style=f"bold {theme.ORANGE}")
    tagline.append("ss", style=f"bold {theme.TEXT_SECONDARY}")
    return tagline

# Menu cards

class MenuCard:
    """A single menu card."""
    
    def __init__(self, key: str, icon: str, title: str, description: str, status: str = None):
        self.key = key
        self.icon = icon
        self.title = title
        self.description = description
        self.status = status
    
    def render(self, active: bool = False, width: int = 24) -> Panel:
        """Render the card as a Rich Panel."""
        
        # Determine styling based on active state
        if active:
            border_style = Style(color=theme.ORANGE, bold=True)
            bg_style = theme.BG_CARD_ACTIVE
            title_style = Style(color=theme.TEXT_PRIMARY, bold=True)
        else:
            border_style = Style(color=theme.BORDER)
            bg_style = theme.BG_CARD
            title_style = Style(color=theme.TEXT_SECONDARY)
        
        # Build card content
        content = Text()
        
        # Icon (large, centered)
        content.append(f"\n  {self.icon}\n\n", style=f"bold {theme.ORANGE if active else theme.TEXT_SECONDARY}")
        
        # Title
        content.append(f"  {self.title}\n", style=title_style)
        
        # Description (wrapped)
        desc_style = Style(color=theme.TEXT_DIM)
        content.append(f"  {self.description}\n", style=desc_style)
        
        # Status badge line (always render for consistent height)
        content.append(f"\n  ", style="")
        if self.status:
            content.append(f" {self.status} ", style=f"bold on {theme.SUCCESS}")
        else:
            content.append("   ", style="")  # Empty placeholder for consistent height
        
        content.append("\n", style="")
        
        # Key hint at bottom
        key_text = Text()
        key_text.append(f"  [{self.key}]", style=f"bold {theme.ORANGE}" if active else f"dim {theme.TEXT_DIM}")
        content.append(key_text)
        content.append("\n", style="")
        
        return Panel(
            content,
            box=THIN_BOX,
            border_style=border_style,
            width=width,
            padding=(0, 1),
        )

# Dashboard

class Dashboard:
    """Main dashboard interface."""
    
    def __init__(self, console: Console):
        self.console = console
        self.selected = 0
        self.running = True
        
        # Define menu cards
        self.cards = [
            MenuCard("1", "🎯", "API Attack", "Precision unlock", None),
            MenuCard("2", "🌾", "Farmer", "Farm engagement", None),
            MenuCard("3", "🤖", "UI Bot", "Screen automation", None),
            MenuCard("4", "📊", "Stats", "Check account", None),
            MenuCard("5", "🔓", "Unlock", "Flash sequence", None),
            MenuCard("6", "⚙️", "Settings", "Configure", "✓" if config.is_configured() else None),
        ]
    
    def render_header(self) -> Panel:
        """Render the header with gradient logo."""
        header_content = Group(
            Align.center(get_gradient_logo()),
            Align.center(get_tagline()),
            Align.center(Text("\"Engineering spite into bootloader freedom\"\n", style=f"italic {theme.TEXT_DIM}")),
        )
        
        return Panel(
            header_content,
            box=box.DOUBLE,
            border_style=theme.BORDER,
            padding=(0, 2),
        )
    
    def render_cards(self) -> Columns:
        """Render the card grid (3 cards per row)."""
        # Row 1: Cards 0, 1, 2
        row1 = [self.cards[i].render(active=(self.selected == i), width=26) for i in range(3)]
        # Row 2: Cards 3, 4, 5
        row2 = [self.cards[i].render(active=(self.selected == i), width=26) for i in range(3, 6)]
        
        return Group(
            Columns(row1, equal=True, expand=True),
            Text(""),  # Spacer
            Columns(row2, equal=True, expand=True),
        )
    
    def render_status_bar(self) -> Panel:
        """Render the bottom status bar."""
        # Left: Exit hint
        left = Text()
        left.append(" [", style=theme.ORANGE)
        left.append("0", style=f"bold {theme.ORANGE}")
        left.append("] ", style=theme.ORANGE)
        left.append("Exit", style=theme.TEXT_SECONDARY)
        
        # Center: Connection status
        center = Text()
        if config.is_configured():
            center.append("● ", style=theme.SUCCESS)
            center.append("Token Configured", style=theme.TEXT_SECONDARY)
        else:
            center.append("○ ", style=theme.ERROR)
            center.append("Token Missing", style=theme.TEXT_SECONDARY)
        
        # Right: Version info
        right = Text()
        right.append("v", style=theme.TEXT_DIM)
        right.append(__version__, style=theme.ORANGE)
        
        # Build table for layout
        table = Table(show_header=False, box=None, expand=True, padding=0)
        table.add_column("left", justify="left", ratio=1)
        table.add_column("center", justify="center", ratio=2)
        table.add_column("right", justify="right", ratio=1)
        table.add_row(left, center, right)
        
        return Panel(
            table,
            box=box.HORIZONTALS,
            border_style=theme.BORDER,
            style=f"on {theme.BG_DEEP}",
            padding=(0, 1),
        )
    
    def render(self) -> Group:
        """Render the complete dashboard."""
        return Group(
            self.render_header(),
            Text(""),  # Spacer
            self.render_cards(),
            Text(""),  # Spacer
            self.render_status_bar(),
        )
    
    def show(self):
        """Display the dashboard and handle input."""
        clear_screen()
        
        # Render static dashboard
        self.console.print(self.render())
        
        # Get input
        self.console.print()
        choice = Prompt.ask(
            f"[{theme.ORANGE}]▶[/]",
            choices=["0", "1", "2", "3", "4", "5", "6"],
            default="0",
            show_choices=False
        )
        
        return choice

# Attack UI

def render_attack_dashboard(stats: dict, elapsed: float, status: str = "WAITING") -> Panel:
    """Render the attack mode dashboard."""
    
    # Status indicator
    if status == "WAITING":
        status_text = Text("⏳ WAITING", style=f"bold {theme.WARNING}")
    elif status == "ATTACKING":
        status_text = Text("🔥 ATTACKING", style=f"bold {theme.ERROR}")
    elif status == "SUCCESS":
        status_text = Text("🎉 SUCCESS!", style=f"bold {theme.SUCCESS}")
    else:
        status_text = Text(status, style=f"bold {theme.TEXT_SECONDARY}")
    
    # Stats table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("label", style=theme.TEXT_DIM)
    table.add_column("value", style=f"bold {theme.TEXT_PRIMARY}")
    
    table.add_row("Status", status_text)
    table.add_row("Elapsed", f"{elapsed:.2f}s")
    table.add_row("", "")
    table.add_row("Total Requests", str(stats.get('total', 0)))
    table.add_row("Code 0 (Success)", Text(str(stats.get('code_0', 0)), style=theme.SUCCESS))
    table.add_row("Code 3 (Full)", Text(str(stats.get('code_3', 0)), style=theme.WARNING))
    table.add_row("Code 6 (Retry)", Text(str(stats.get('code_6', 0)), style=theme.TEXT_SECONDARY))
    table.add_row("Errors", Text(str(stats.get('errors', 0)), style=theme.ERROR))
    
    # Progress bar for requests
    if stats.get('total', 0) > 0:
        success_rate = (stats.get('code_0', 0) / stats['total']) * 100
        bar_width = 30
        filled = int((success_rate / 100) * bar_width)
        bar = Text()
        bar.append("█" * filled, style=theme.SUCCESS)
        bar.append("░" * (bar_width - filled), style=theme.TEXT_DIM)
        bar.append(f" {success_rate:.1f}%", style=theme.TEXT_SECONDARY)
        table.add_row("", "")
        table.add_row("Success Rate", bar)
    
    return Panel(
        Align.center(table),
        title=f"[bold {theme.ORANGE}]🎯 API ATTACK[/]",
        border_style=theme.ORANGE,
        box=box.DOUBLE,
        padding=(1, 2),
    )

def render_farmer_dashboard(stats: dict, limits: dict, elapsed: float, status: str = "FARMING", last_action: str = "") -> Panel:
    """Render the Ghost Farmer dashboard."""
    
    # Status indicator
    if status == "FARMING":
        status_text = Text("🌾 FARMING", style=f"bold {theme.SUCCESS}")
    elif status == "PAUSED":
        status_text = Text("⏸️ PAUSED", style=f"bold {theme.WARNING}")
    elif status == "COMPLETE":
        status_text = Text("✅ COMPLETE", style=f"bold {theme.SUCCESS}")
    elif status == "SLEEPING":
        status_text = Text("😴 SLEEPING (Caps Hit)", style=f"bold {theme.TEXT_SECONDARY}")
    else:
        status_text = Text(status, style=f"bold {theme.TEXT_SECONDARY}")
    
    # Stats table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("label", style=theme.TEXT_DIM)
    table.add_column("value", style=f"bold {theme.TEXT_PRIMARY}")
    table.add_column("progress", style=theme.TEXT_SECONDARY)
    
    table.add_row("Status", status_text, "")
    table.add_row("Elapsed", f"{int(elapsed // 3600)}h {int((elapsed % 3600) // 60)}m {int(elapsed % 60)}s", "")
    table.add_row("", "", "")
    
    # Progress bars for each action type
    actions = [
        ("❤️ Likes", 'likes', theme.ERROR),
        ("💬 Comments", 'comments', theme.ORANGE),
        ("🔄 Shares", 'shares', theme.WARNING),
    ]
    
    for label, key, color in actions:
        current = stats.get(key, 0)
        limit = limits.get(key, 5)
        pct = min(100, (current / limit) * 100) if limit > 0 else 100
        bar_width = 15
        filled = int((pct / 100) * bar_width)
        
        bar = Text()
        bar.append("█" * filled, style=color)
        bar.append("░" * (bar_width - filled), style=theme.TEXT_DIM)
        bar.append(f" {current}/{limit}", style=theme.TEXT_SECONDARY)
        
        table.add_row(label, bar, "✓" if current >= limit else "")
    
    table.add_row("", "", "")
    table.add_row("🔧 Tasks", str(stats.get('tasks', 0)), "")
    table.add_row("❌ Errors", Text(str(stats.get('errors', 0)), style=theme.ERROR if stats.get('errors', 0) > 0 else theme.TEXT_DIM), "")
    
    if last_action:
        table.add_row("", "", "")
        table.add_row("Last Action", Text(last_action[:40], style=theme.TEXT_DIM), "")
    
    return Panel(
        Align.center(table),
        title=f"[bold {theme.ORANGE}]🌾 GHOST FARMER[/]",
        border_style=theme.ORANGE,
        box=box.DOUBLE,
        padding=(1, 2),
    )

def render_ui_bot_dashboard(stats: dict, elapsed: float, status: str = "RUNNING", last_action: str = "", device_info: str = "") -> Panel:
    """Render the UI Bot dashboard."""
    
    # Status indicator
    if status == "RUNNING":
        status_text = Text("🤖 RUNNING", style=f"bold {theme.SUCCESS}")
    elif status == "PAUSED":
        status_text = Text("⏸️ PAUSED", style=f"bold {theme.WARNING}")
    elif status == "COMPLETE":
        status_text = Text("✅ COMPLETE", style=f"bold {theme.SUCCESS}")
    elif status == "NO_DEVICE":
        status_text = Text("❌ NO DEVICE", style=f"bold {theme.ERROR}")
    else:
        status_text = Text(status, style=f"bold {theme.TEXT_SECONDARY}")
    
    # Stats table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("label", style=theme.TEXT_DIM)
    table.add_column("value", style=f"bold {theme.TEXT_PRIMARY}")
    
    table.add_row("Status", status_text)
    table.add_row("Elapsed", f"{int(elapsed // 3600)}h {int((elapsed % 3600) // 60)}m {int(elapsed % 60)}s")
    if device_info:
        table.add_row("Device", Text(device_info, style=theme.TEXT_SECONDARY))
    table.add_row("", "")
    
    # Stats
    table.add_row("📜 Scrolls", str(stats.get('scrolls', 0)))
    table.add_row("👁️ Views", str(stats.get('views', 0)))
    table.add_row("❤️ Likes", str(stats.get('likes', 0)))
    table.add_row("💬 Comments", str(stats.get('comments', 0)))
    table.add_row("🔄 Restarts", Text(str(stats.get('restarts', 0)), style=theme.WARNING if stats.get('restarts', 0) > 0 else theme.TEXT_DIM))
    table.add_row("❌ Errors", Text(str(stats.get('errors', 0)), style=theme.ERROR if stats.get('errors', 0) > 0 else theme.TEXT_DIM))
    
    if last_action:
        table.add_row("", "")
        table.add_row("Last Action", Text(last_action[:40], style=theme.TEXT_DIM))
    
    return Panel(
        Align.center(table),
        title=f"[bold {theme.ORANGE}]🤖 UI BOT[/]",
        border_style=theme.ORANGE,
        box=box.DOUBLE,
        padding=(1, 2),
    )

# Core functions

def run_attack(console: Console, target_hour: int = 17, threads: int = 100, immediate: bool = False):
    """Run the API attack with live dashboard."""
    import requests
    clear_screen()
    
    API_URL = "https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth"
    
    if not config.is_configured():
        console.print(Panel(
            "[bold red]❌ Tokens not configured![/]\n\nRun Settings first to configure your tokens.",
            border_style="red"
        ))
        return
    
    headers = config.get_headers()
    
    # State
    stop_event = threading.Event()
    stats = {'total': 0, 'code_0': 0, 'code_3': 0, 'code_6': 0, 'errors': 0, 'winner': None}
    stats_lock = threading.Lock()
    
    def send_request(thread_id):
        session = requests.Session()
        session.headers.update(headers)
        payload = {"is_retry": False}
        
        while not stop_event.is_set():
            try:
                payload["is_retry"] = not payload["is_retry"]
                resp = session.post(API_URL, json=payload, timeout=2)
                
                with stats_lock:
                    stats['total'] += 1
                    if resp.status_code == 200:
                        data = resp.json()
                        code = data.get('code', -1)
                        result = data.get('data', {}).get('apply_result', -1) if data.get('data') else -1
                        
                        if code == 0:
                            stats['code_0'] += 1
                            if result == 1:
                                stats['winner'] = {'thread': thread_id, 'data': data}
                                stop_event.set()
                        elif code == 3 or result == 3:
                            stats['code_3'] += 1
                        elif code == 6 or result == 6:
                            stats['code_6'] += 1
                    else:
                        stats['errors'] += 1
            except:
                with stats_lock:
                    stats['errors'] += 1
            time.sleep(0.001)
    
    # Target time
    now = datetime.now()
    if immediate:
        target_time = now
        launch_time = now
    else:
        target_time = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)
        launch_time = target_time - timedelta(seconds=1.5)
        
    
    # Show countdown
    clear_screen()
    console.print(Panel(
        f"[bold]Target Time:[/] {target_time.strftime('%H:%M:%S')}\n"
        f"[bold]Launch Time:[/] {launch_time.strftime('%H:%M:%S.%f')[:-3]} (1.5s buffer)\n"
        f"[bold]Threads:[/] {threads}",
        title=f"[{theme.ORANGE}]🎯 API Attack Configuration[/]",
        border_style=theme.ORANGE
    ))
    
    if not immediate:
        # Countdown with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style=theme.ORANGE, finished_style=theme.SUCCESS),
            TextColumn("[bold]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            total = (launch_time - datetime.now()).total_seconds()
            if total > 0:
                task = progress.add_task(f"[{theme.ORANGE}]Countdown...[/]", total=total)
                while datetime.now() < launch_time:
                    remaining = (launch_time - datetime.now()).total_seconds()
                    progress.update(task, completed=total - remaining)
                    time.sleep(0.1)
    
    # Launch threads
    console.print(f"\n[bold {theme.ERROR}]🚀 LAUNCHING ATTACK![/]\n")
    
    for i in range(threads):
        t = threading.Thread(target=send_request, args=(i,), daemon=True)
        t.start()
    
    start_time = datetime.now()
    
    # Live dashboard
    with Live(console=console, refresh_per_second=10) as live:
        while not stop_event.is_set():
            elapsed = (datetime.now() - start_time).total_seconds()
            
            with stats_lock:
                current_stats = stats.copy()
            
            status = "SUCCESS" if current_stats.get('winner') else "ATTACKING"
            live.update(render_attack_dashboard(current_stats, elapsed, status))
            
            if elapsed > 30:
                stop_event.set()
            
            time.sleep(0.05)
    
    # Final result
    console.print()
    if stats.get('winner'):
        console.print(Panel(
            f"[bold green]🎉 VICTORY! TICKET ACQUIRED![/]\n\n"
            f"Thread: {stats['winner']['thread']}\n"
            f"Requests: {stats['total']}\n"
            f"Time: {(datetime.now() - start_time).total_seconds():.3f}s",
            border_style=theme.SUCCESS,
            title="[bold]SUCCESS[/]"
        ))
    else:
        console.print(Panel(
            f"Attack completed. Quota may have been full.\n"
            f"Total requests: {stats['total']}",
            border_style=theme.WARNING,
            title="[bold]Results[/]"
        ))

def run_stats(console: Console):
    """Check account stats with styled output."""
    import requests
    clear_screen()
    
    if not config.is_configured():
        console.print(Panel(
            "[bold red]❌ Tokens not configured![/]",
            border_style="red"
        ))
        return
    
    console.print(f"\n[{theme.ORANGE}]📊 Fetching stats...[/]\n")
    
    url = "https://sgp-api.buy.mi.com/bbs/api/global/user/data"
    
    try:
        resp = requests.get(url, headers=config.get_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                user = data.get('data', {})
                level = user.get('level_info', {})
                
                table = Table(box=THIN_BOX, border_style=theme.ORANGE)
                table.add_column("Property", style=theme.TEXT_DIM)
                table.add_column("Value", style=f"bold {theme.TEXT_PRIMARY}")
                
                table.add_row("Username", user.get('user_name', '—'))
                table.add_row("Level", f"{level.get('level', '?')} ({level.get('level_title', '')})")
                table.add_row("Points", str(user.get('point', 0)))
                table.add_row("XP", f"{level.get('current_value', 0)} / {level.get('max_value', 0)}")
                table.add_row("Comments", str(user.get('comment_count', 0)))
                
                console.print(Panel(table, title=f"[{theme.ORANGE}]Account Stats[/]", border_style=theme.ORANGE))
                console.print(f"\n[{theme.SUCCESS}]✓ Token is valid![/]")
            else:
                console.print(f"[{theme.ERROR}]❌ Error: {data.get('msg', 'Unknown')}[/]")
                if data.get('code') == 100004:
                    console.print(f"[{theme.WARNING}]Token expired - re-extract via mitmproxy[/]")
    except Exception as e:
        console.print(f"[{theme.ERROR}]❌ Error: {e}[/]")

def run_settings(console: Console):
    """Settings with styled interface."""
    clear_screen()
    console.print(Panel(
        f"[bold]Token Status:[/] {'[green]✓ Configured[/]' if config.is_configured() else '[red]✗ Not configured[/]'}\n\n"
        f"[dim]Tokens are loaded from TOKENS_BACKUP.json[/]",
        title=f"[{theme.ORANGE}]⚙️ Settings[/]",
        border_style=theme.ORANGE
    ))
    
    if not config.is_configured():
        console.print(f"\n[{theme.WARNING}]To configure tokens:[/]")
        console.print("1. Use mitmproxy to intercept Xiaomi Community app")
        console.print("2. Extract tokens to TOKENS_BACKUP.json")
        console.print("3. Restart this tool")

def run_farmer(console: Console, hours: int = 24):
    """Run the Ghost Farmer with live Rich dashboard."""
    import requests
    import random
    clear_screen()
    
    BASE_URL = "https://sgp-api.buy.mi.com/bbs/api/global"
    
    # Comment templates
    COMMENTS = [
        "Nice post!", "Great share!", "Thanks for this info.", 
        "Very helpful.", "Awesome!", "Cool.", "Looks good.", 
        "Interesting read.", "Good one.", "Appreciate it.",
        "Wow!", "Nice capture.", "Amazing.", "Top tier.",
        "Love this.", "Keep it up.", "Useful.", "Fantastic."
    ]
    
    if not config.is_configured():
        console.print(Panel(
            "[bold red]❌ Tokens not configured![/]\n\nRun Settings first to configure your tokens.",
            border_style="red"
        ))
        return
    
    headers = config.get_headers()
    session = requests.Session()
    session.headers.update(headers)
    
    # Daily limits (posts removed - farmer doesn't create posts)
    limits = {'likes': 5, 'comments': 5, 'shares': 3}
    stats = {'likes': 0, 'comments': 0, 'shares': 0, 'posts': 0, 'tasks': 0, 'errors': 0}
    stop_event = threading.Event()
    last_action = ""
    
    def fetch_feed():
        """Fetch post IDs from feed."""
        endpoints = [
            f"{BASE_URL}/thread/appHome/hot-board",
            f"{BASE_URL}/thread/appHome/index?limit=20",
        ]
        
        for url in endpoints:
            try:
                resp = session.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('code') == 0:
                        raw_items = data.get('data')
                        items = []
                        if isinstance(raw_items, list):
                            items = raw_items
                        elif isinstance(raw_items, dict):
                            items = raw_items.get('list') or raw_items.get('records') or []
                        
                        post_ids = []
                        for item in items:
                            pid = item.get('id') or item.get('thread_id') or item.get('aid')
                            if pid:
                                post_ids.append(pid)
                        if post_ids:
                            return post_ids
            except:
                pass
        return [1869950, 1869951, 1869952]  # Fallback
    
    def like_post(aid):
        nonlocal last_action
        if stats['likes'] >= limits['likes']:
            return False
        try:
            time.sleep(random.uniform(0.5, 1))
            resp = session.post(f"{BASE_URL}/action/like", json={"aid": int(aid), "action": True})
            if resp.status_code == 200:
                stats['likes'] += 1
                last_action = f"❤️ Liked post {aid}"
                return True
        except:
            stats['errors'] += 1
        return False
    
    def comment_post(aid):
        nonlocal last_action
        if stats['comments'] >= limits['comments']:
            return False
        try:
            text = random.choice(COMMENTS)
            time.sleep(random.uniform(0.5, 1.5))
            resp = session.post(f"{BASE_URL}/comment/add", json={"text": text, "aid": int(aid)})
            if resp.status_code == 200:
                stats['comments'] += 1
                last_action = f"💬 '{text}' on {aid}"
                return True
        except:
            stats['errors'] += 1
        return False
    
    def share_post(aid):
        nonlocal last_action
        if stats['shares'] >= limits['shares']:
            return False
        try:
            session.get(f"{BASE_URL}/thread/share?aid={aid}")
            stats['shares'] += 1
            last_action = f"🔄 Shared post {aid}"
            return True
        except:
            stats['errors'] += 1
        return False
    
    def finish_task(task_id):
        try:
            session.post(f"{BASE_URL}/task/finish", json={"task_id": task_id})
            stats['tasks'] += 1
        except:
            pass
    
    # Show config
    console.print(Panel(
        f"[bold]Duration:[/] {hours} hours\n"
        f"[bold]Daily Caps:[/] {limits['likes']} likes, {limits['comments']} comments, {limits['shares']} shares\n"
        f"[bold]Token:[/] {'✓ Valid' if config.is_configured() else '✗ Invalid'}",
        title=f"[{theme.ORANGE}]🌾 Ghost Farmer Configuration[/]",
        border_style=theme.ORANGE
    ))
    
    if not Confirm.ask(f"\n[{theme.ORANGE}]Start farming?[/]", default=True):
        return
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=hours)
    
    console.print(f"\n[bold {theme.SUCCESS}]🌾 STARTING GHOST FARMER![/]\n")
    
    def farm_loop():
        nonlocal last_action
        while not stop_event.is_set() and datetime.now() < end_time:
            # Check if all caps hit
            if all(stats[k] >= limits[k] for k in limits):
                last_action = "😴 Daily caps hit, sleeping..."
                time.sleep(60)
                continue
            
            # Fetch posts
            posts = fetch_feed()
            if not posts:
                time.sleep(30)
                continue
            
            # Interact with posts
            for aid in posts:
                if stop_event.is_set() or datetime.now() >= end_time:
                    break
                
                # Random action selection
                if stats['shares'] < limits['shares'] and random.random() < 0.3:
                    share_post(aid)
                elif stats['comments'] < limits['comments'] and random.random() < 0.4:
                    if comment_post(aid):
                        finish_task(6)
                elif stats['likes'] < limits['likes']:
                    if like_post(aid):
                        finish_task(4)
                
                # Human-like delay
                time.sleep(random.uniform(1, 3))
            
            time.sleep(5)  # Batch delay
    
    # Start farm thread
    farm_thread = threading.Thread(target=farm_loop, daemon=True)
    farm_thread.start()
    
    # Live dashboard
    try:
        with Live(console=console, refresh_per_second=2) as live:
            while farm_thread.is_alive() and not stop_event.is_set():
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Determine status
                all_caps = all(stats[k] >= limits[k] for k in limits)
                status = "SLEEPING" if all_caps else "FARMING"
                
                live.update(render_farmer_dashboard(stats, limits, elapsed, status, last_action))
                time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()
    
    # Final result
    console.print()
    console.print(Panel(
        f"[bold green]🌾 Farming session complete![/]\n\n"
        f"❤️ Likes: {stats['likes']}/{limits['likes']}\n"
        f"💬 Comments: {stats['comments']}/{limits['comments']}\n"
        f"🔄 Shares: {stats['shares']}/{limits['shares']}\n"
        f"🔧 Tasks: {stats['tasks']}\n"
        f"❌ Errors: {stats['errors']}",
        border_style=theme.SUCCESS,
        title="[bold]Results[/]"
    ))

def run_ui_bot(console: Console):
    """Run the UI Bot with configuration menu."""
    import subprocess
    clear_screen()
    
    ADB_PATH = os.path.expanduser("~/Downloads/platform-tools/adb")
    PACKAGE_NAME = "com.mi.global.bbs"
    
    # Check ADB connection
    def check_device():
        try:
            result = subprocess.run(
                f"sudo {ADB_PATH} devices", 
                shell=True, capture_output=True, text=True, timeout=5
            )
            return "device" in result.stdout and "offline" not in result.stdout
        except:
            return False
    
    def get_device_info():
        try:
            result = subprocess.run(
                f"sudo {ADB_PATH} shell getprop ro.product.model",
                shell=True, capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except:
            return "Unknown"
    
    # Show sub-menu
    while True:
        clear_screen()
        
        device_connected = check_device()
        device_info = get_device_info() if device_connected else "Not connected"
        
        console.print(Panel(
            Group(
                Text("🤖 UI BOT CONTROLLER\n", style=f"bold {theme.ORANGE}"),
                Text(f"Device: ", style=theme.TEXT_DIM),
                Text(f"{device_info}\n", style=theme.SUCCESS if device_connected else theme.ERROR),
                Text(f"Status: ", style=theme.TEXT_DIM),
                Text("● Connected" if device_connected else "○ Disconnected", 
                     style=theme.SUCCESS if device_connected else theme.ERROR),
            ),
            border_style=theme.ORANGE,
            box=box.DOUBLE,
        ))
        
        console.print(f"\n[{theme.BORDER}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
        console.print(f"[{theme.TEXT_SECONDARY}][1] 🎯 Run Calibration[/]")
        console.print(f"[{theme.TEXT_SECONDARY}][2] ⚡ Test Run (5 min)[/]")
        console.print(f"[{theme.TEXT_SECONDARY}][3] 🌾 Full Session (48 hours)[/]")
        console.print(f"[{theme.TEXT_DIM}][0] ← Back[/]\n")
        
        choice = Prompt.ask(f"[{theme.ORANGE}]Select[/]", choices=["0", "1", "2", "3"], default="0")
        
        if choice == "0":
            break
        
        if not device_connected:
            console.print(f"\n[{theme.ERROR}]❌ No device connected![/]")
            console.print(f"[{theme.TEXT_DIM}]Connect your device via USB with debugging enabled.[/]")
            Prompt.ask(f"\n[{theme.TEXT_DIM}]Press Enter...[/]")
            continue
        
        bot_script = SCRIPT_DIR / "src" / "ui_bot.py"
        if not bot_script.exists():
            console.print(f"\n[{theme.ERROR}]❌ src/ui_bot.py not found![/]")
            Prompt.ask(f"\n[{theme.TEXT_DIM}]Press Enter...[/]")
            continue
        
        if choice == "1":
            # Run calibration
            console.print(f"\n[{theme.ORANGE}]🎯 Launching calibration wizard...[/]")
            console.print(f"[{theme.TEXT_DIM}]A GUI window will open for each button.[/]\n")
            os.system(f"python3 {bot_script} --calibrate")
            Prompt.ask(f"\n[{theme.TEXT_DIM}]Press Enter to continue...[/]")
        
        elif choice == "2":
            # Test run
            console.print(f"\n[{theme.ORANGE}]⚡ Starting 5-minute test session...[/]\n")
            os.system(f"python3 {bot_script} --test")
            Prompt.ask(f"\n[{theme.TEXT_DIM}]Press Enter to continue...[/]")
        
        elif choice == "3":
            # Full session
            hours = IntPrompt.ask("Session duration (hours)", default=48)
            console.print(f"\n[{theme.ORANGE}]🌾 Starting {hours}-hour farming session...[/]\n")
            os.system(f"python3 {bot_script} --hours {hours}")
            Prompt.ask(f"\n[{theme.TEXT_DIM}]Press Enter to continue...[/]")

# Setup wizard

def run_setup_wizard(console: Console) -> bool:
    """
    First-run setup wizard. Shows when TOKENS_BACKUP.json doesn't exist.
    Returns True if setup completed, False if skipped.
    """
    clear_screen()
    
    # Header
    console.print(Panel(
        Group(
            Align.center(get_gradient_logo()),
            Align.center(Text("\n🔧 FIRST-TIME SETUP", style=f"bold {theme.ORANGE}")),
            Align.center(Text("Let's configure your tokens to get started\n", style=theme.TEXT_DIM)),
        ),
        box=box.DOUBLE,
        border_style=theme.ORANGE,
        padding=(1, 2),
    ))
    
    console.print(f"\n[{theme.TEXT_SECONDARY}]This wizard will help you set up the required authentication tokens.[/]")
    console.print(f"[{theme.TEXT_DIM}]You'll need to extract these using mitmproxy from the Xiaomi Community app.[/]\n")
    
    console.print(f"[{theme.WARNING}]📋 Required tokens:[/]")
    console.print(f"  • [bold]new_bbs_serviceToken[/] - Main authentication cookie")
    console.print(f"  • [bold]deviceId[/] - Your device identifier")
    console.print(f"  • [bold]x-csrf-token[/] - CSRF protection token (optional)\n")
    
    # Ask if ready
    if not Confirm.ask(f"[{theme.ORANGE}]Do you have these tokens ready?[/]", default=False):
        console.print(f"\n[{theme.TEXT_DIM}]No problem! Here's how to get them:[/]\n")
        console.print(f"[{theme.TEXT_SECONDARY}]1.[/] Install mitmproxy: [cyan]pip install mitmproxy[/]")
        console.print(f"[{theme.TEXT_SECONDARY}]2.[/] Patch the Xiaomi Community APK to bypass SSL pinning")
        console.print(f"[{theme.TEXT_SECONDARY}]3.[/] Run mitmproxy and configure your device to use it")
        console.print(f"[{theme.TEXT_SECONDARY}]4.[/] Open the app and navigate to bootloader unlock")
        console.print(f"[{theme.TEXT_SECONDARY}]5.[/] Look for requests to [cyan]sgp-api.buy.mi.com[/]")
        console.print(f"[{theme.TEXT_SECONDARY}]6.[/] Extract the Cookie and x-csrf-token headers\n")
        console.print(f"[{theme.TEXT_DIM}]See MITM_AND_API_GUIDE.md for detailed instructions.[/]\n")
        
        Prompt.ask(f"[{theme.TEXT_DIM}]Press Enter to continue without setup[/]")
        return False
    
    # Collect tokens
    console.print(f"\n[{theme.ORANGE}]Enter your tokens below:[/]\n")
    
    service_token = Prompt.ask(
        f"[{theme.TEXT_SECONDARY}]new_bbs_serviceToken[/]",
        default=""
    )
    
    device_id = Prompt.ask(
        f"[{theme.TEXT_SECONDARY}]deviceId[/]",
        default=""
    )
    
    csrf_token = Prompt.ask(
        f"[{theme.TEXT_SECONDARY}]x-csrf-token[/] [dim](optional)[/]",
        default=""
    )
    
    if not service_token:
        console.print(f"\n[{theme.ERROR}]❌ Service token is required![/]")
        Prompt.ask(f"[{theme.TEXT_DIM}]Press Enter to continue without setup[/]")
        return False
    
    # Build config structure (matches TOKENS_BACKUP.example.json schema)
    config_data = {
        "authentication": {
            "new_bbs_serviceToken": service_token,
            "x-csrf-token": csrf_token,
        },
        "device": {
            "deviceId": device_id,
            "versionCode": "500429",
            "versionName": "5.4.29"
        },
        "api": {
            "base_url": "https://sgp-api.buy.mi.com/bbs/api/global",
            "unlock_endpoint": "/apply/bl-auth"
        }
    }
    
    # Save to file
    try:
        with open(TOKENS_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        console.print(f"\n[{theme.SUCCESS}]✅ Configuration saved to TOKENS_BACKUP.json![/]")
        
        # Reload config
        global config
        config = Config()
        
        Prompt.ask(f"\n[{theme.TEXT_DIM}]Press Enter to continue to main menu[/]")
        return True
        
    except Exception as e:
        console.print(f"\n[{theme.ERROR}]❌ Failed to save config: {e}[/]")
        Prompt.ask(f"[{theme.TEXT_DIM}]Press Enter to continue[/]")
        return False

# Terminal resize

def resize_terminal(cols: int = 100, rows: int = 42):
    """
    Resize terminal using ANSI escape sequence (XTerm control sequence).
    Format: ESC [ 8 ; <rows> ; <cols> t
    
    Works on: xterm, gnome-terminal, konsole, xfce4-terminal, and most
    modern terminal emulators. May not work on pure Wayland without XWayland.
    """
    import shutil
    import signal
    
    # Check current terminal size first
    current = shutil.get_terminal_size()
    if current.columns >= cols and current.lines >= rows:
        return True  # Already big enough
    
    # Set up SIGWINCH handler to prevent script interruption after resize
    original_handler = signal.getsignal(signal.SIGWINCH)
    signal.signal(signal.SIGWINCH, lambda signum, frame: None)  # Ignore the signal
    
    try:
        # Send the XTerm resize escape sequence
        # \x1b[8;<rows>;<cols>t - this is the standard CSI sequence for window resize
        sys.stdout.write(f"\x1b[8;{rows};{cols}t")
        sys.stdout.flush()
        time.sleep(0.2)  # Give terminal time to process
        
        # Check if it worked
        new_size = shutil.get_terminal_size()
        return new_size.columns >= cols - 5 and new_size.lines >= rows - 5
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGWINCH, original_handler)

# Main

def main():
    console = Console()
    
    parser = argparse.ArgumentParser(description="⚔️ XBLBSMA")
    subparsers = parser.add_subparsers(dest="command")
    
    attack_p = subparsers.add_parser("attack")
    attack_p.add_argument("--hour", type=int, default=17)
    attack_p.add_argument("--threads", type=int, default=100)
    attack_p.add_argument("--now", action="store_true")
    
    farmer_p = subparsers.add_parser("farmer")
    farmer_p.add_argument("--hours", type=int, default=24)
    
    subparsers.add_parser("bot")
    subparsers.add_parser("stats")
    subparsers.add_parser("settings")
    
    args = parser.parse_args()
    
    if args.command == "attack":
        run_attack(console, args.hour, args.threads, args.now)
    elif args.command == "farmer":
        run_farmer(console, args.hours)
    elif args.command == "bot":
        run_ui_bot(console)
    elif args.command == "stats":
        run_stats(console)
    elif args.command == "settings":
        run_settings(console)
    else:
        # Interactive menu
        resize_terminal(100, 42)  # Resize terminal to fit dashboard
        
        # Run setup wizard if config file doesn't exist
        if not TOKENS_FILE.exists():
            run_setup_wizard(console)
        
        dashboard = Dashboard(console)
        
        while True:
            clear_screen()
            choice = dashboard.show()
            
            if choice == "0":
                console.print(f"\n[{theme.ORANGE}]Goodbye! May your bootloader be forever unlocked. ⚔️[/]\n")
                break
            elif choice == "1":
                hour = IntPrompt.ask("Target hour", default=17)
                threads = IntPrompt.ask("Threads", default=100)
                immediate = Confirm.ask("Attack immediately?", default=False)
                run_attack(console, hour, threads, immediate)
            elif choice == "2":
                hours = IntPrompt.ask("Farming duration (hours)", default=24)
                run_farmer(console, hours)
            elif choice == "3":
                run_ui_bot(console)
            elif choice == "4":
                run_stats(console)
            elif choice == "5":
                script = SCRIPT_DIR / "scripts" / "unlock_day.sh"
                if script.exists():
                    # Show unlock submenu
                    console.print(f"\n[{theme.ORANGE}]🔓 UNLOCK DAY MENU[/]")
                    console.print(f"[{theme.BORDER}]━━━━━━━━━━━━━━━━━━━━━━[/]")
                    console.print(f"[{theme.TEXT_SECONDARY}][1] Verify Prerequisites[/]")
                    console.print(f"[{theme.TEXT_SECONDARY}][2] Backup Device[/]")
                    console.print(f"[{theme.WARNING}][3] UNLOCK Bootloader[/]")
                    console.print(f"[{theme.TEXT_SECONDARY}][4] Flash TWRP + Custom ROM[/]")
                    console.print(f"[{theme.SUCCESS}][5] Full Sequence (backup → unlock → flash)[/]")
                    console.print(f"[{theme.TEXT_SECONDARY}][6] Post-flash Setup[/]")
                    console.print(f"[{theme.TEXT_DIM}][0] Back[/]\n")
                    
                    unlock_choice = Prompt.ask(f"[{theme.ORANGE}]Select[/]", default="0")
                    
                    flag_map = {
                        "1": "--verify",
                        "2": "--backup", 
                        "3": "--unlock",
                        "4": "--flash",
                        "5": "--full",
                        "6": "--post",
                    }
                    
                    if unlock_choice in flag_map:
                        clear_screen()
                        os.system(f"bash {script} {flag_map[unlock_choice]}")
                else:
                    console.print(f"[{theme.ERROR}]scripts/unlock_day.sh not found![/]")
            elif choice == "6":
                run_settings(console)
            
            Prompt.ask(f"\n[{theme.TEXT_DIM}]Press Enter...[/]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        console = Console()
        console.print(f"\n\n[{XiaomiTheme.ORANGE}]👋 Interrupted. Goodbye![/]\n")
        sys.exit(0)
