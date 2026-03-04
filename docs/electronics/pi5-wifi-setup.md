# Pi 5 WiFi Setup (Raspberry Pi OS / Debian Trixie)

## Problem

Fresh Raspberry Pi OS (2025-12-04, based on Debian Trixie) on Pi 5: wifi interface `wlan0` stuck as `unavailable` in NetworkManager despite working hardware.

## Root Causes

1. **Soft-blocked by rfkill on every boot** — `rfkill list` showed `phy0: Soft blocked: yes`. Unblocking didn't persist.
2. **NetworkManager not managing wlan0** — `/etc/NetworkManager/NetworkManager.conf` had `[ifupdown] managed=false`. Changing to `true` didn't help either; NM continued to report `unavailable`.
3. **No dhcpcd systemd unit** — dhcpcd was installed (`/usr/sbin/dhcpcd`) but had no systemd service file, so it never started on boot.

Notably, `iw dev wlan0 scan` worked fine throughout — the hardware and driver (brcmfmac, BCM4345/6) were functional. The issue was purely in the network management stack.

## Solution: Bypass NetworkManager, use wpa_supplicant + dhcpcd

### 1. Mask rfkill so wifi stays unblocked

```bash
sudo rfkill unblock wifi
sudo systemctl mask systemd-rfkill.service systemd-rfkill.socket
```

### 2. Configure wpa_supplicant

Create `/etc/wpa_supplicant/wpa_supplicant-wlan0.conf` (note the `-wlan0` suffix — required by the systemd template unit):

```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_SSID"
    psk=YOUR_PSK_HASH
}
```

Generate the PSK hash with: `wpa_passphrase "SSID" "password"`

Enable the service:

```bash
sudo systemctl enable wpa_supplicant@wlan0
```

### 3. Create a dhcpcd systemd service for wlan0

`/etc/systemd/system/dhcpcd-wlan0.service`:

```ini
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
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable dhcpcd-wlan0
```

### 4. Reboot and verify

```bash
sudo reboot
# From laptop:
ping emiglio.local
ssh mark@emiglio.local
```

## Notes

- The Pi 5's built-in wifi (BCM43455, 802.11ac dual-band) works fine — the issue is NM on this OS image.
- The `nl80211: kernel reports: Registration to specific type not supported` warning from wpa_supplicant is harmless.
- Pi 5 MAC prefix for wifi: `2C:CF:67`.
- Assigned IP via DHCP: check with `ip addr show wlan0`.
