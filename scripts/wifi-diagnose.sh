#!/usr/bin/env bash
# wifi-diagnose.sh — Pi 5 wifi diagnostic script
# Run on the Pi: bash scripts/wifi-diagnose.sh
# Collects all relevant wifi state for troubleshooting.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ $1${NC}"; }
fail() { echo -e "  ${RED}✗ $1${NC}"; }
warn() { echo -e "  ${YELLOW}! $1${NC}"; }
header() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }

ISSUES=0

header "1. Interface exists"
if ip link show wlan0 &>/dev/null; then
    pass "wlan0 exists"
    STATE=$(ip -br link show wlan0 | awk '{print $2}')
    if [[ "$STATE" == "UP" ]]; then
        pass "wlan0 is UP"
    else
        fail "wlan0 state: $STATE (expected UP)"
        ((ISSUES++))
    fi
else
    fail "wlan0 not found — no wifi hardware detected"
    ((ISSUES++))
fi

header "2. rfkill"
if command -v rfkill &>/dev/null; then
    RFKILL_OUT=$(rfkill -J 2>/dev/null || rfkill list wifi)
    SOFT=$(rfkill list wifi | grep -i "Soft blocked" | head -1 | awk '{print $NF}')
    HARD=$(rfkill list wifi | grep -i "Hard blocked" | head -1 | awk '{print $NF}')
    if [[ "$SOFT" == "no" && "$HARD" == "no" ]]; then
        pass "wifi not blocked"
    else
        fail "wifi blocked — soft=$SOFT hard=$HARD"
        ((ISSUES++))
    fi
    # Check if rfkill service is masked
    if systemctl is-enabled systemd-rfkill.service 2>/dev/null | grep -q masked; then
        pass "systemd-rfkill.service is masked (won't re-block on boot)"
    else
        warn "systemd-rfkill.service NOT masked — wifi may get re-blocked on reboot"
        ((ISSUES++))
    fi
else
    warn "rfkill not installed"
fi

header "3. wpa_supplicant"
# Config file
if [[ -f /etc/wpa_supplicant/wpa_supplicant-wlan0.conf ]]; then
    pass "wpa_supplicant-wlan0.conf exists"
    if grep -q "ssid=" /etc/wpa_supplicant/wpa_supplicant-wlan0.conf; then
        SSID=$(grep "ssid=" /etc/wpa_supplicant/wpa_supplicant-wlan0.conf | head -1 | sed 's/.*ssid="\(.*\)"/\1/')
        pass "configured SSID: $SSID"
    else
        fail "no SSID configured in wpa_supplicant-wlan0.conf"
        ((ISSUES++))
    fi
else
    fail "missing /etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
    ((ISSUES++))
fi
# Service
WPA_ENABLED=$(systemctl is-enabled wpa_supplicant@wlan0 2>/dev/null || echo "not-found")
WPA_ACTIVE=$(systemctl is-active wpa_supplicant@wlan0 2>/dev/null || echo "not-found")
if [[ "$WPA_ENABLED" == "enabled" ]]; then
    pass "wpa_supplicant@wlan0 enabled"
else
    fail "wpa_supplicant@wlan0 not enabled (is: $WPA_ENABLED)"
    ((ISSUES++))
fi
if [[ "$WPA_ACTIVE" == "active" ]]; then
    pass "wpa_supplicant@wlan0 running"
else
    fail "wpa_supplicant@wlan0 not running (is: $WPA_ACTIVE)"
    ((ISSUES++))
fi

header "4. dhcpcd"
# Service
DHCP_ENABLED=$(systemctl is-enabled dhcpcd-wlan0 2>/dev/null || echo "not-found")
DHCP_ACTIVE=$(systemctl is-active dhcpcd-wlan0 2>/dev/null || echo "not-found")
if [[ "$DHCP_ENABLED" == "enabled" ]]; then
    pass "dhcpcd-wlan0 enabled"
else
    fail "dhcpcd-wlan0 not enabled (is: $DHCP_ENABLED)"
    ((ISSUES++))
fi
if [[ "$DHCP_ACTIVE" == "active" ]]; then
    pass "dhcpcd-wlan0 running"
else
    fail "dhcpcd-wlan0 not running (is: $DHCP_ACTIVE)"
    ((ISSUES++))
fi
# Unit file
if [[ -f /etc/systemd/system/dhcpcd-wlan0.service ]]; then
    pass "dhcpcd-wlan0.service unit file exists"
else
    fail "missing /etc/systemd/system/dhcpcd-wlan0.service"
    ((ISSUES++))
fi

header "5. IP address"
IP=$(ip -4 addr show wlan0 2>/dev/null | grep -oP 'inet \K[\d.]+' || echo "")
if [[ -n "$IP" ]]; then
    pass "wlan0 IP: $IP"
else
    fail "wlan0 has no IPv4 address"
    ((ISSUES++))
fi

header "6. DNS"
if [[ -f /etc/resolv.conf ]]; then
    NS=$(grep "^nameserver" /etc/resolv.conf | head -1 | awk '{print $2}')
    if [[ -n "$NS" ]]; then
        pass "nameserver: $NS"
    else
        fail "/etc/resolv.conf has no nameserver entries"
        ((ISSUES++))
    fi
else
    fail "/etc/resolv.conf missing"
    ((ISSUES++))
fi
if [[ -f /etc/resolv.conf.head ]]; then
    pass "/etc/resolv.conf.head exists (persistent DNS)"
else
    warn "/etc/resolv.conf.head missing — DNS may not survive reboot"
    ((ISSUES++))
fi
# Test resolution
if host api.anthropic.com &>/dev/null 2>&1 || ping -c1 -W2 api.anthropic.com &>/dev/null 2>&1; then
    pass "DNS resolution working (api.anthropic.com)"
else
    fail "DNS resolution FAILED for api.anthropic.com"
    ((ISSUES++))
fi

header "7. Connectivity"
if ping -c1 -W3 8.8.8.8 &>/dev/null; then
    pass "internet reachable (8.8.8.8)"
else
    fail "cannot reach 8.8.8.8"
    ((ISSUES++))
fi
if ping -c1 -W3 api.anthropic.com &>/dev/null; then
    pass "api.anthropic.com reachable"
else
    fail "api.anthropic.com NOT reachable"
    ((ISSUES++))
fi

header "8. Ethernet (conflict check)"
ETH_IP=$(ip -4 addr show eth0 2>/dev/null | grep -oP 'inet \K[\d.]+' || echo "")
if [[ -n "$ETH_IP" ]]; then
    warn "ethernet is ALSO connected (eth0: $ETH_IP) — may mask wifi issues"
else
    pass "ethernet not connected (testing wifi only)"
fi

header "Summary"
if [[ $ISSUES -eq 0 ]]; then
    echo -e "${GREEN}All checks passed — wifi should be working.${NC}"
else
    echo -e "${RED}Found $ISSUES issue(s). Run: bash scripts/wifi-fix.sh${NC}"
fi
