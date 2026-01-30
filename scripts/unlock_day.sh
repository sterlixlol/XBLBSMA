#!/bin/bash
# ============================================================================
#  ⚔️  OPERATION SPITE - ULTIMATE BOOTLOADER UNLOCK & FLASH SCRIPT  ⚔️
# ============================================================================
#  This script automates the entire unlock and flash process for Xiaomi Pad 6
#  Device Codename: xun
#  
#  Prerequisites:
#  - Bootloader unlock ticket acquired (check with --verify)
#  - 72-hour waiting period completed
#  - Device connected via USB with USB debugging enabled
#  - All required files in the xiaomi/ subdirectory
#
#  Usage:
#    ./unlock_day.sh --verify     # Check if everything is ready
#    ./unlock_day.sh --backup     # Backup device before unlock
#    ./unlock_day.sh --unlock     # UNLOCK BOOTLOADER (irreversible!)
#    ./unlock_day.sh --flash      # Flash TWRP + EvolutionX + Magisk
#    ./unlock_day.sh --full       # Full sequence (backup -> unlock -> flash)
#
#  Author: sterlix (with spite-driven motivation)
#  Created: 2026-01-29
# ============================================================================

set -e  # Exit on error

# ============================================================================
# CONFIGURATION
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
XIAOMI_DIR="$SCRIPT_DIR/xiaomi"
BACKUP_DIR="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
ADB_PATH="$HOME/Downloads/platform-tools/adb"
FASTBOOT_PATH="$HOME/Downloads/platform-tools/fastboot"

# Files
TWRP_IMG="$XIAOMI_DIR/twrp/twrp_3.7.1_xun.img"
EVOLUTION_ZIP="$XIAOMI_DIR/evolutionx/EvolutionX-14.0-20240715-xun-v9.2-Unofficial.zip"
MAGISK_APK="$XIAOMI_DIR/magisk/Magisk-v30.6.apk"
OVERCLOCK_APK="$XIAOMI_DIR/overclock/app-release.apk"

# Device
DEVICE_CODENAME="xun"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_banner() {
    echo -e "${RED}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║   ⚔️   OPERATION SPITE - BOOTLOADER UNLOCK SCRIPT   ⚔️            ║"
    echo "║                                                                   ║"
    echo "║   \"Never underestimate a developer with spite and Python\"        ║"
    echo "║                                                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${WHITE}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

confirm() {
    echo -e "${YELLOW}"
    read -p "⚠️  $1 (yes/no): " response
    echo -e "${NC}"
    if [[ "$response" != "yes" ]]; then
        echo "Aborted."
        exit 1
    fi
}

wait_for_device() {
    local mode=$1
    local timeout=${2:-60}
    local count=0
    
    echo -n "Waiting for device in $mode mode"
    while [ $count -lt $timeout ]; do
        if [ "$mode" = "adb" ]; then
            if sudo $ADB_PATH devices | grep -q "device$"; then
                echo ""
                print_success "Device detected!"
                return 0
            fi
        elif [ "$mode" = "fastboot" ]; then
            if sudo $FASTBOOT_PATH devices | grep -q "fastboot"; then
                echo ""
                print_success "Device detected in fastboot mode!"
                return 0
            fi
        fi
        echo -n "."
        sleep 1
        ((count++))
    done
    
    echo ""
    print_error "Timeout waiting for device in $mode mode"
    return 1
}

# ============================================================================
# VERIFICATION
# ============================================================================

verify_prerequisites() {
    print_step "🔍 VERIFYING PREREQUISITES"
    
    local all_good=true
    
    # Check ADB
    if [ -f "$ADB_PATH" ]; then
        print_success "ADB found at $ADB_PATH"
    else
        print_error "ADB not found at $ADB_PATH"
        all_good=false
    fi
    
    # Check Fastboot
    if [ -f "$FASTBOOT_PATH" ]; then
        print_success "Fastboot found at $FASTBOOT_PATH"
    else
        print_error "Fastboot not found at $FASTBOOT_PATH"
        all_good=false
    fi
    
    # Check TWRP
    if [ -f "$TWRP_IMG" ]; then
        local size=$(du -h "$TWRP_IMG" | cut -f1)
        print_success "TWRP recovery found ($size)"
    else
        print_error "TWRP not found: $TWRP_IMG"
        all_good=false
    fi
    
    # Check EvolutionX
    if [ -f "$EVOLUTION_ZIP" ]; then
        local size=$(du -h "$EVOLUTION_ZIP" | cut -f1)
        print_success "EvolutionX ROM found ($size)"
    else
        print_error "EvolutionX not found: $EVOLUTION_ZIP"
        all_good=false
    fi
    
    # Check Magisk
    if [ -f "$MAGISK_APK" ]; then
        local size=$(du -h "$MAGISK_APK" | cut -f1)
        print_success "Magisk found ($size)"
    else
        print_warning "Magisk not found (optional): $MAGISK_APK"
    fi
    
    # Check device connection
    echo ""
    print_info "Checking device connection..."
    if sudo $ADB_PATH devices | grep -q "device$"; then
        print_success "Device connected via ADB"
        
        # Get device info
        local model=$(sudo $ADB_PATH shell getprop ro.product.model 2>/dev/null | tr -d '\r')
        local android=$(sudo $ADB_PATH shell getprop ro.build.version.release 2>/dev/null | tr -d '\r')
        local codename=$(sudo $ADB_PATH shell getprop ro.product.device 2>/dev/null | tr -d '\r')
        
        echo ""
        print_info "Device Model: $model"
        print_info "Android Version: $android"
        print_info "Device Codename: $codename"
        
        if [ "$codename" != "$DEVICE_CODENAME" ]; then
            print_warning "Device codename ($codename) differs from expected ($DEVICE_CODENAME)"
        fi
    else
        print_warning "No device connected via ADB"
        print_info "Connect your device with USB debugging enabled"
    fi
    
    echo ""
    if [ "$all_good" = true ]; then
        print_success "All prerequisites verified! You're ready for unlock day! 🎉"
        return 0
    else
        print_error "Some prerequisites are missing. Please fix them before proceeding."
        return 1
    fi
}

verify_ticket() {
    print_step "🎫 VERIFYING BOOTLOADER UNLOCK TICKET"
    
    print_info "Checking ticket status via API..."
    
    # Use the check_stats.py or similar to verify
    if [ -f "$SCRIPT_DIR/check_stats.py" ]; then
        python3 "$SCRIPT_DIR/check_stats.py"
    fi
    
    echo ""
    print_info "To manually verify your ticket:"
    print_info "1. Open Xiaomi Community app"
    print_info "2. Go to Me → Unlock Bootloader"
    print_info "3. Confirm ticket shows 'Valid until 01/29/2027'"
    
    echo ""
    print_warning "IMPORTANT: 72-hour waiting period"
    print_info "Ticket acquired: 2026-01-29 17:00:00"
    print_info "Earliest unlock: 2026-02-01 17:00:00"
}

# ============================================================================
# BACKUP
# ============================================================================

backup_device() {
    print_step "💾 BACKING UP DEVICE"
    
    # Check device connection
    if ! sudo $ADB_PATH devices | grep -q "device$"; then
        print_error "No device connected!"
        exit 1
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    print_info "Backup directory: $BACKUP_DIR"
    
    # Backup app list
    echo ""
    print_info "Backing up installed apps list..."
    sudo $ADB_PATH shell pm list packages -3 > "$BACKUP_DIR/user_apps.txt"
    print_success "App list saved ($(wc -l < "$BACKUP_DIR/user_apps.txt") apps)"
    
    # Backup device info
    print_info "Backing up device information..."
    sudo $ADB_PATH shell getprop > "$BACKUP_DIR/device_properties.txt"
    print_success "Device properties saved"
    
    # Backup storage
    echo ""
    print_info "Backing up internal storage (this may take a while)..."
    print_warning "Note: Some system folders may fail - this is normal"
    
    sudo $ADB_PATH pull /sdcard/ "$BACKUP_DIR/sdcard/" 2>/dev/null || true
    
    local sdcard_size=$(du -sh "$BACKUP_DIR/sdcard" 2>/dev/null | cut -f1)
    print_success "Internal storage backed up ($sdcard_size)"
    
    # Full ADB backup (optional, often incomplete on Android 12+)
    echo ""
    print_info "Creating ADB backup (press 'Back up my data' on device if prompted)..."
    sudo $ADB_PATH backup -apk -shared -all -f "$BACKUP_DIR/full_backup.ab" 2>/dev/null || true
    
    # Summary
    echo ""
    print_success "Backup complete!"
    print_info "Backup location: $BACKUP_DIR"
    ls -lh "$BACKUP_DIR"
}

# ============================================================================
# UNLOCK BOOTLOADER
# ============================================================================

unlock_bootloader() {
    print_step "🔓 UNLOCKING BOOTLOADER"
    
    echo -e "${RED}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                         ⚠️  WARNING ⚠️                             ║"
    echo "╠═══════════════════════════════════════════════════════════════════╣"
    echo "║  THIS ACTION WILL:                                                ║"
    echo "║  • WIPE ALL DATA on your device                                   ║"
    echo "║  • Void your warranty (if any)                                    ║"
    echo "║  • Cannot be undone without reflashing stock ROM                  ║"
    echo "║                                                                   ║"
    echo "║  Make sure you have:                                              ║"
    echo "║  ✓ Backed up all important data                                   ║"
    echo "║  ✓ At least 50% battery                                           ║"
    echo "║  ✓ 72 hours have passed since ticket acquisition                  ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    confirm "Are you ABSOLUTELY SURE you want to unlock the bootloader?"
    confirm "Type 'yes' again to confirm you have backed up your data"
    
    # Reboot to bootloader
    print_info "Rebooting to bootloader mode..."
    sudo $ADB_PATH reboot bootloader
    
    wait_for_device "fastboot" 30
    
    # Check fastboot connection
    print_info "Checking fastboot connection..."
    sudo $FASTBOOT_PATH devices
    
    # Get unlock status
    print_info "Checking current unlock status..."
    sudo $FASTBOOT_PATH oem device-info 2>&1 || true
    
    echo ""
    print_warning "Attempting to unlock bootloader..."
    
    # Try both unlock methods (different devices use different commands)
    if sudo $FASTBOOT_PATH flashing unlock 2>&1; then
        print_success "Bootloader unlock command sent!"
    elif sudo $FASTBOOT_PATH oem unlock 2>&1; then
        print_success "Bootloader unlock command sent (oem method)!"
    else
        print_error "Unlock command failed!"
        print_info "You may need to confirm on the device screen"
    fi
    
    echo ""
    print_warning "CHECK YOUR DEVICE SCREEN!"
    print_info "If prompted, use volume buttons to select 'Unlock' and power to confirm"
    
    read -p "Press Enter after confirming on device..."
    
    # Verify unlock status
    print_info "Verifying unlock status..."
    sudo $FASTBOOT_PATH oem device-info 2>&1 || true
    
    echo ""
    print_success "Bootloader unlock process complete!"
    print_info "Your device will reboot and factory reset"
    print_warning "This is normal - all data will be wiped"
}

# ============================================================================
# FLASH CUSTOM ROM
# ============================================================================

flash_recovery() {
    print_step "📀 FLASHING TWRP RECOVERY"
    
    if ! sudo $FASTBOOT_PATH devices | grep -q "fastboot"; then
        print_info "Device not in fastboot mode. Rebooting..."
        sudo $ADB_PATH reboot bootloader 2>/dev/null || true
        wait_for_device "fastboot" 30
    fi
    
    print_info "Flashing TWRP recovery..."
    sudo $FASTBOOT_PATH flash recovery "$TWRP_IMG"
    
    print_success "TWRP flashed successfully!"
    
    echo ""
    print_info "Booting into TWRP..."
    print_warning "IMPORTANT: Hold Volume Up + Power while device reboots"
    print_warning "Or the stock recovery will overwrite TWRP!"
    
    # Boot directly into recovery
    sudo $FASTBOOT_PATH boot "$TWRP_IMG"
    
    print_info "Waiting for TWRP to boot..."
    sleep 10
}

flash_rom() {
    print_step "📱 FLASHING EVOLUTIONX ROM"
    
    print_info "Pushing EvolutionX to device..."
    print_warning "This is a 2.1GB file - please be patient..."
    
    sudo $ADB_PATH push "$EVOLUTION_ZIP" /sdcard/
    
    print_success "ROM pushed to device!"
    
    echo ""
    print_info "In TWRP, you need to:"
    echo "  1. Go to 'Wipe'"
    echo "  2. Select 'Advanced Wipe'"
    echo "  3. Check: Dalvik/ART Cache, System, Data, Cache"
    echo "  4. Swipe to wipe"
    echo "  5. Go back, then 'Install'"
    echo "  6. Select 'EvolutionX-14.0-20240715-xun-v9.2-Unofficial.zip'"
    echo "  7. Swipe to flash"
    
    read -p "Press Enter after flashing the ROM..."
    
    print_success "ROM should now be flashed!"
}

flash_magisk() {
    print_step "🔐 INSTALLING MAGISK (ROOT)"
    
    if [ ! -f "$MAGISK_APK" ]; then
        print_warning "Magisk APK not found, skipping..."
        return
    fi
    
    print_info "Pushing Magisk to device..."
    sudo $ADB_PATH push "$MAGISK_APK" /sdcard/
    
    print_success "Magisk pushed!"
    
    echo ""
    print_info "To install Magisk:"
    echo "  1. In TWRP, select 'Install'"
    echo "  2. Navigate to /sdcard/"
    echo "  3. Select Magisk-v30.6.apk"
    echo "  4. Swipe to flash"
    echo ""
    echo "  After ROM boot:"
    echo "  5. Open Magisk app"
    echo "  6. Complete the setup"
    
    read -p "Press Enter when ready to continue..."
}

push_extras() {
    print_step "📦 PUSHING EXTRA FILES"
    
    # Push overclock app
    if [ -f "$OVERCLOCK_APK" ]; then
        print_info "Pushing overclock tool..."
        sudo $ADB_PATH push "$OVERCLOCK_APK" /sdcard/
        print_success "Overclock tool pushed!"
    fi
    
    print_success "All extras pushed to device!"
}

# ============================================================================
# FULL SEQUENCE
# ============================================================================

full_sequence() {
    print_banner
    
    echo -e "${PURPLE}${BOLD}"
    echo "🚀 FULL UNLOCK & FLASH SEQUENCE"
    echo "================================"
    echo ""
    echo "This will perform the complete sequence:"
    echo "  1. Verify prerequisites"
    echo "  2. Backup device data"
    echo "  3. Unlock bootloader (DATA WIPE!)"
    echo "  4. Flash TWRP recovery"
    echo "  5. Flash EvolutionX ROM"
    echo "  6. Install Magisk (root)"
    echo "  7. Push extras (overclock tool)"
    echo -e "${NC}"
    
    confirm "Are you ready to begin the full sequence?"
    
    verify_prerequisites || exit 1
    
    echo ""
    confirm "Prerequisites verified. Proceed with backup?"
    backup_device
    
    echo ""
    confirm "Backup complete. Proceed with BOOTLOADER UNLOCK?"
    unlock_bootloader
    
    echo ""
    confirm "Bootloader unlocked. Proceed with flashing?"
    flash_recovery
    flash_rom
    flash_magisk
    push_extras
    
    print_step "🎉 SEQUENCE COMPLETE!"
    
    echo -e "${GREEN}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║   🎉  CONGRATULATIONS!  🎉                                        ║"
    echo "║                                                                   ║"
    echo "║   Your Xiaomi Pad 6 is now running:                               ║"
    echo "║   • EvolutionX 14.0 v9.2                                          ║"
    echo "║   • TWRP Recovery 3.7.1                                           ║"
    echo "║   • Magisk v30.6 (root)                                           ║"
    echo "║                                                                   ║"
    echo "║   Xiaomi's engagement farming system: DEFEATED                    ║"
    echo "║   Your spite-driven victory: COMPLETE                             ║"
    echo "║                                                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ============================================================================
# POST-FLASH SETUP
# ============================================================================

post_flash_setup() {
    print_step "⚡ POST-FLASH OPTIMIZATION"
    
    print_info "Waiting for device to boot..."
    wait_for_device "adb" 120
    
    print_info "Installing Magisk app..."
    sudo $ADB_PATH install -r "$MAGISK_APK" 2>/dev/null || true
    
    print_info "Installing overclock tool..."
    sudo $ADB_PATH install -r "$OVERCLOCK_APK" 2>/dev/null || true
    
    print_success "Apps installed!"
    
    echo ""
    print_info "Recommended post-flash setup:"
    echo "  1. Open Magisk and complete initial setup"
    echo "  2. Grant root to overclock app"
    echo "  3. Set CPU governor to 'performance'"
    echo "  4. Overclock GPU (carefully!)"
    echo "  5. Enjoy your FREE tablet! 🔥"
}

# ============================================================================
# MAIN
# ============================================================================

print_banner

case "${1:-}" in
    --verify|-v)
        verify_prerequisites
        verify_ticket
        ;;
    --backup|-b)
        backup_device
        ;;
    --unlock|-u)
        unlock_bootloader
        ;;
    --flash|-f)
        flash_recovery
        flash_rom
        flash_magisk
        push_extras
        ;;
    --full)
        full_sequence
        ;;
    --post)
        post_flash_setup
        ;;
    --help|-h|*)
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --verify, -v    Verify all prerequisites and ticket status"
        echo "  --backup, -b    Backup device data before unlock"
        echo "  --unlock, -u    UNLOCK BOOTLOADER (irreversible, data wipe!)"
        echo "  --flash,  -f    Flash TWRP + EvolutionX + Magisk"
        echo "  --full          Complete sequence (backup → unlock → flash)"
        echo "  --post          Post-flash setup (install apps)"
        echo "  --help,  -h     Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 --verify     # Check if ready for unlock day"
        echo "  $0 --backup     # Backup before the big day"
        echo "  $0 --full       # Do everything (unlock day!)"
        echo ""
        echo "⚔️  OPERATION SPITE - Defeat engagement farming through engineering"
        ;;
esac
