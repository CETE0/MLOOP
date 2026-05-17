#!/usr/bin/env bash
set -euo pipefail

# MLOOP Install Script
# Installs MLOOP on a Raspberry Pi running Raspberry Pi OS Lite Bookworm

echo "=== MLOOP Installer ==="

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Check for Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: This does not appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Installing dependencies..."
apt-get update
apt-get install -y mpv python3 python3-pip python3-venv

echo ""
echo "Creating mloop user..."
if ! id -u mloop >/dev/null 2>&1; then
    useradd --system --create-home mloop
fi

echo ""
echo "Creating directories..."
mkdir -p /etc/mloop
mkdir -p /var/lib/mloop
mkdir -p /run/mloop
mkdir -p /home/mloop/media

chown mloop:mloop /var/lib/mloop
chown mloop:mloop /home/mloop/media

echo ""
echo "Installing MLOOP..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

python3 -m venv /opt/mloop/venv
/opt/mloop/venv/bin/pip install -e .

ln -sf /opt/mloop/venv/bin/mloopd /usr/bin/mloopd

echo ""
echo "Installing configuration..."
if [ ! -f /etc/mloop/config.toml ]; then
    cp config/mloop.example.toml /etc/mloop/config.toml
fi

echo ""
echo "Installing systemd service..."
cp packaging/systemd/mloop.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable mloop

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Add media files to /home/mloop/media/"
echo "2. Edit /etc/mloop/config.toml if needed"
echo "3. Start the service: sudo systemctl start mloop"
echo "4. Check status: sudo systemctl status mloop"
