# XBLBSMA

> **X**iaomi **B**oot**L**oader **B**ull**S**hit **M**y **A**ss

```
██╗  ██╗██████╗ ██╗     ██████╗ ███████╗███╗   ███╗ █████╗ 
╚██╗██╔╝██╔══██╗██║     ██╔══██╗██╔════╝████╗ ████║██╔══██╗
 ╚███╔╝ ██████╔╝██║     ██████╔╝███████╗██╔████╔██║███████║
 ██╔██╗ ██╔══██╗██║     ██╔══██╗╚════██║██║╚██╔╝██║██╔══██║
██╔╝ ██╗██████╔╝███████╗██████╔╝███████║██║ ╚═╝ ██║██║  ██║
╚═╝  ╚═╝╚═════╝ ╚══════╝╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝
```

[![License: WTFPL](https://img.shields.io/badge/License-WTFPL-brightgreen.svg)](http://www.wtfpl.net/about/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)]()

---

## What is this?

**A comprehensive toolkit to bypass Xiaomi's arbitrary "engagement farming" requirements for bootloader unlocking.**

Xiaomi requires users to:
1. Reach Level 5 in their community app
2. Farm "Community Points" through likes, comments, and shares
3. Compete for **limited daily unlock slots** that fill up in milliseconds

This project automates the entire process and **snipes unlock slots with surgical precision**.

---

## ⚡ Features

| Feature | Description |
|---------|-------------|
| **Premium Terminal UI** | Beautiful Rich-powered interface with Xiaomi orange theme |
| **Ghost Farmer** | API-based engagement farming (no device needed!) |
| **UI Bot** | ADB screen automation fallback with visual calibration |
| **API Attack** | Multi-threaded unlock slot sniper (100+ concurrent requests) |
| **Live Dashboards** | Real-time progress tracking for all operations |
| **Unlock Day Script** | Full unlock + custom ROM flash sequence |

---

## Quick Start

### 1. Install Dependencies

```bash
git clone https://github.com/sterlixlol/xblbsma.git
cd xblbsma
pip install -r requirements.txt
```

### 2. Extract Your Tokens

Follow the [MITM Guide](docs/MITM_AND_API_GUIDE.md) to:
1. Patch the Xiaomi Community APK (bypass SSL pinning)
2. Intercept API traffic with mitmproxy
3. Extract your `new_bbs_serviceToken` and `x-csrf-token`

```bash
cp TOKENS_BACKUP.example.json TOKENS_BACKUP.json
# Edit TOKENS_BACKUP.json with your extracted tokens
```

### 3. Launch XBLBSMA

```bash
python3 xblbsma.py
```

---

## 📖 Usage

### Interactive Menu

```
┌──────────────────────────────────────────────────────┐
│  [1] 🎯 API Attack    - Snipe unlock slots           │
│  [2] 🌾 Farmer        - Farm engagement points       │
│  [3] 🤖 UI Bot        - ADB screen automation        │
│  [4] 📊 Stats         - Check account status         │
│  [5] 🔓 Unlock        - Bootloader unlock sequence   │
│  [6] ⚙️ Settings      - Configure tokens             │
└──────────────────────────────────────────────────────┘
```

### CLI Commands

```bash
# Launch interactive menu
python3 xblbsma.py

# Run farmer for 24 hours
python3 xblbsma.py farmer --hours 24

# Launch UI bot submenu
python3 xblbsma.py bot

# Schedule attack for 5PM
python3 xblbsma.py attack --hour 17

# Attack immediately (for testing)
python3 xblbsma.py attack --now

# Check account stats
python3 xblbsma.py stats
```

---

## The Attack Strategy

Xiaomi releases **limited unlock slots daily at a fixed time** (usually 5:00 PM local). The slots fill up in **~500ms**. 

Our attack strategy:

1. **Pre-buffer**: Start 1.5 seconds before target time
2. **Multi-threading**: 100+ concurrent request threads
3. **Zero-delay flooding**: Hammer the API endpoint
4. **Smart detection**: Distinguish between "Success", "Quota Full", and "Retry"

```
┌─────────────────────────────────────────────────────┐
│  🎯 API ATTACK                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Status:      🔥 ATTACKING                          │
│  Elapsed:     2.34s                                 │
│                                                     │
│  Total Requests:  4,521                             │
│  Code 0 (Success): 2,103                            │
│  Code 3 (Full):    2,418                            │
│  Errors:           0                                │
│                                                     │
│  Success Rate: ████████████░░░░░░ 46.5%             │
└─────────────────────────────────────────────────────┘
```

---

## Farming Strategy

The Ghost Farmer directly calls Xiaomi's API to:

- ❤️ Like posts (5/day)
- 💬 Comment on posts (5/day)  
- 🔄 Share posts (3/day)
- 📝 Create posts (5/day)

All with human-like delays and daily cap management.

---

## Project Structure

```
XBLBSMA/
├── xblbsma.py                    # Main unified interface
├── requirements.txt              # Python dependencies
├── TOKENS_BACKUP.example.json    # Token template
│
├── src/                          # Core modules
│   ├── attack.py                 # API attack script
│   ├── farmer.py                 # Ghost farmer
│   ├── ui_bot.py                 # ADB UI automation
│   └── stats.py                  # Account stats checker
│
├── scripts/                      # Shell scripts
│   └── unlock_day.sh             # Unlock + flash script
│
└── docs/                         # Documentation
    └── MITM_AND_API_GUIDE.md     # Token extraction guide
```

---

## Requirements

- **Python 3.10+**
- **ADB** (only for UI Bot) - [Download Platform Tools](https://developer.android.com/studio/releases/platform-tools)
- **mitmproxy** (for token extraction) - `pip install mitmproxy`

---

## 🛡️ Disclaimer

This project is for **educational purposes only**. 

- You are solely responsible for how you use this tool
- Bootloader unlocking may void your warranty
- Xiaomi may change their API at any time
- This project is not affiliated with Xiaomi

---

## License

```
            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
```

---

## 🙏 Acknowledgments

- **Spite** - The primary motivator for this entire project
- **Xiaomi** - For creating such a needlessly complicated unlock process
- **The open source community** - For mitmproxy, Rich, and other amazing tools

---

<p align="center">
  <b>Made with 🧡 and an unreasonable amount of spite</b>
</p>
