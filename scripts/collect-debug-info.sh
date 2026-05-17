#!/usr/bin/env bash
set -euo pipefail

# MLOOP Debug Info Collection Script
# Collects system information for troubleshooting

echo "=== MLOOP Debug Info ==="
echo "Collected: $(date)"
echo ""

echo "--- System Information ---"
uname -a
echo ""

echo "--- OS Release ---"
cat /etc/os-release 2>/dev/null || echo "Not available"
echo ""

echo "--- MLOOP Service Status ---"
systemctl status mloop --no-pager 2>/dev/null || echo "Service not found or not running"
echo ""

echo "--- Recent MLOOP Logs ---"
journalctl -u mloop -n 300 --no-pager 2>/dev/null || echo "Logs not available"
echo ""

echo "--- DRM Connectors ---"
ls -la /sys/class/drm/ 2>/dev/null || echo "DRM not available"
echo ""

echo "--- HDMI Status ---"
cat /sys/class/drm/card*-HDMI-A-*/status 2>/dev/null || echo "No HDMI connectors found"
echo ""

echo "--- HDMI Modes ---"
cat /sys/class/drm/card*-HDMI-A-*/modes 2>/dev/null || echo "No HDMI modes found"
echo ""

echo "--- kmsprint Connectors ---"
kmsprint 2>/dev/null | grep Connector || echo "kmsprint not available"
echo ""

echo "--- Audio Devices (aplay) ---"
aplay -l 2>/dev/null || echo "aplay not available"
echo ""

echo "--- Audio Devices (PipeWire) ---"
wpctl status 2>/dev/null || echo "PipeWire not available"
echo ""

echo "--- Audio Devices (PulseAudio) ---"
pactl info 2>/dev/null || echo "PulseAudio not available"
echo ""

echo "--- mpv Version ---"
mpv --version 2>/dev/null || echo "mpv not installed"
echo ""

echo "--- cvlc Version ---"
cvlc --version 2>/dev/null || echo "cvlc not installed"
echo ""

echo "--- MLOOP Configuration ---"
cat /etc/mloop/config.toml 2>/dev/null || echo "Config not found"
echo ""

echo "=== End of Debug Info ==="
