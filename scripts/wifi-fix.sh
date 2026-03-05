#!/usr/bin/env bash
# wifi-fix.sh — Apply all known Pi 5 wifi fixes
# Run on the Pi: sudo bash scripts/wifi-fix.sh
# See docs/electronics/pi5-wifi-setup.md for background.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() { echo -e "\n${YELLOW}>>> $1${NC}"; }
ok()   { echo -e "${GREEN}    done${NC}"; }

if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Run as root: sudo bash $0${NC}"
    exit 1
fi

# ── 1. Unblock wifi and mask rfkill ──────────────────────────────────
step "1/7  Unblocking wifi + masking systemd-rfkill"
rfkill unblock wifi
systemctl mask systemd-rfkill.service systemd-rfkill.socket 2>/dev/null || true
ok

# ── 2. Bring interface up ────────────────────────────────────────────
step "2/7  Bringing wlan0 up"
ip link set wlan0 up
ok

# ── 3. wpa_supplicant config ─────────────────────────────────────────
step "3/7  Checking wpa_supplicant config"
WPA_CONF="/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
if [[ -f "$WPA_CONF" ]]; then
    echo "    $WPA_CONF exists"
    SSID=$(grep "ssid=" "$WPA_CONF" | head -1 | sed 's/.*ssid="\(.*\)"/\1/')
    echo "    SSID: $SSID"
else
    echo -e "${RED}    Missing $WPA_CONF — creating template${NC}"
    cat > "$WPA_CONF" <<'WPAEOF'
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_SSID"
    psk=YOUR_PSK_HASH
}
WPAEOF
    echo -e "${RED}    EDIT $WPA_CONF with your SSID/PSK, then re-run this script${NC}"
    echo "    Generate PSK: wpa_passphrase \"SSID\" \"password\""
    exit 1
fi

# ── 4. wpa_supplicant service ────────────────────────────────────────
step "4/7  Enabling wpa_supplicant@wlan0"
systemctl daemon-reload
systemctl enable wpa_supplicant@wlan0
systemctl restart wpa_supplicant@wlan0
# Wait for association
echo "    Waiting for wifi association (up to 15s)..."
for i in $(seq 1 15); do
    if iw dev wlan0 link 2>/dev/null | grep -q "Connected"; then
        echo -e "    ${GREEN}Associated after ${i}s${NC}"
        break
    fi
    sleep 1
done
if ! iw dev wlan0 link 2>/dev/null | grep -q "Connected"; then
    echo -e "    ${YELLOW}Not associated yet — dhcpcd will retry${NC}"
fi
ok

# ── 5. dhcpcd service ───────────────────────────────────────────────
step "5/7  Setting up dhcpcd-wlan0 service"
UNIT="/etc/systemd/system/dhcpcd-wlan0.service"
cat > "$UNIT" <<'UNITEOF'
[Unit]
Description=DHCP client for wlan0
After=wpa_supplicant@wlan0.service
Wants=wpa_supplicant@wlan0.service

[Service]
Type=forking
ExecStartPre=/usr/sbin/rfkill unblock wifi
ExecStartPre=/sbin/ip link set wlan0 up
ExecStartPre=/bin/sleep 5
ExecStart=/usr/sbin/dhcpcd wlan0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNITEOF
systemctl daemon-reload
systemctl enable dhcpcd-wlan0
systemctl restart dhcpcd-wlan0
ok

# ── 6. Late-boot wifi recovery service ──────────────────────────────
step "6/7  Installing wifi-up late-boot recovery service"
# The Pi 5 brcmfmac driver re-applies the rfkill soft-block AFTER
# wpa_supplicant and dhcpcd have already started and unblocked.
# This service waits for boot to settle, then unblocks + restarts
# the wifi stack if needed.
cat > /etc/systemd/system/wifi-up.service <<'WIFIEOF'
[Unit]
Description=Late-boot WiFi recovery (Pi 5 rfkill workaround)
After=multi-user.target dhcpcd-wlan0.service
Wants=dhcpcd-wlan0.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c '\
  sleep 10; \
  if rfkill list wifi | grep -q "Soft blocked: yes"; then \
    echo "wifi-up: rfkill was still blocked, unblocking..."; \
    rfkill unblock wifi; \
    ip link set wlan0 up; \
    sleep 2; \
    systemctl restart wpa_supplicant@wlan0; \
    sleep 5; \
    systemctl restart dhcpcd-wlan0; \
    echo "wifi-up: wifi stack restarted"; \
  else \
    echo "wifi-up: wifi already unblocked, nothing to do"; \
  fi'

[Install]
WantedBy=multi-user.target
WIFIEOF
systemctl daemon-reload
systemctl enable wifi-up
echo "    Installed wifi-up.service (runs 10s after boot, re-unblocks if needed)"
ok

# ── 7. DNS ───────────────────────────────────────────────────────────
step "7/7  Ensuring persistent DNS"
if [[ ! -f /etc/resolv.conf.head ]] || ! grep -q "nameserver" /etc/resolv.conf.head 2>/dev/null; then
    echo "nameserver 8.8.8.8" > /etc/resolv.conf.head
    echo "    Created /etc/resolv.conf.head with nameserver 8.8.8.8"
fi
# Also fix current resolv.conf if empty
if ! grep -q "^nameserver" /etc/resolv.conf 2>/dev/null; then
    echo "nameserver 8.8.8.8" >> /etc/resolv.conf
    echo "    Added nameserver to current /etc/resolv.conf"
fi
ok

# ── Verify ───────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}=== Verifying ===${NC}"
sleep 3

IP=$(ip -4 addr show wlan0 2>/dev/null | grep -oP 'inet \K[\d.]+' || echo "")
if [[ -n "$IP" ]]; then
    echo -e "${GREEN}  wlan0 IP: $IP${NC}"
else
    echo -e "${YELLOW}  No IP yet — may need a few more seconds. Check: ip addr show wlan0${NC}"
fi

if ping -c1 -W3 8.8.8.8 &>/dev/null; then
    echo -e "${GREEN}  Internet: reachable${NC}"
else
    echo -e "${RED}  Internet: NOT reachable${NC}"
fi

if ping -c1 -W3 api.anthropic.com &>/dev/null; then
    echo -e "${GREEN}  DNS: working${NC}"
else
    echo -e "${RED}  DNS: NOT working${NC}"
fi

echo ""
echo -e "${GREEN}Done. Reboot to verify persistence: sudo reboot${NC}"
echo "Then from laptop: ssh mark@emiglio.local"
echo "On Pi after reboot: bash scripts/wifi-diagnose.sh"
