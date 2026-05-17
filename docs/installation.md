# Installation

This guide walks you through installing MLOOP on a Raspberry Pi.

## Prerequisites

- Raspberry Pi 3, 4, or 5
- Raspberry Pi OS Lite Bookworm or newer
- HDMI display
- Storage for media files

## Step 1: Install Raspberry Pi OS Lite

1. Download Raspberry Pi OS Lite (Bookworm) from the [official website](https://www.raspberrypi.com/software/)
2. Flash the image to your SD card using Raspberry Pi Imager
3. Boot the Pi and complete initial setup

## Step 2: Install Dependencies

```bash
sudo apt update
sudo apt install -y mpv python3 python3-pip python3-venv
```

## Step 3: Install MLOOP

```bash
# Clone the repository
git clone https://github.com/yourusername/mloop.git
cd mloop

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install MLOOP
pip install -e .
```

## Step 4: Configure MLOOP

Copy the example configuration:

```bash
sudo mkdir -p /etc/mloop
sudo cp config/mloop.example.toml /etc/mloop/config.toml
```

Edit the configuration file to set your media directory:

```bash
sudo nano /etc/mloop/config.toml
```

## Step 5: Create MLOOP User

```bash
sudo useradd --system --create-home mloop
sudo mkdir -p /home/mloop/media
sudo chown mloop:mloop /home/mloop/media
```

## Step 6: Enable the Service

```bash
sudo cp packaging/systemd/mloop.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mloop
sudo systemctl start mloop
```

## Step 7: Add Media

Copy your media files to the media directory:

```bash
sudo cp /path/to/videos/* /home/mloop/media/
sudo chown mloop:mloop /home/mloop/media/*
```

## Verifying Installation

Check the service status:

```bash
sudo systemctl status mloop
```

View logs:

```bash
sudo journalctl -u mloop -f
```

## Troubleshooting

If MLOOP doesn't start:

1. Check that mpv is installed: `mpv --version`
2. Check that media files exist in the configured directory
3. Check logs: `sudo journalctl -u mloop -n 100`

See [Troubleshooting](troubleshooting.md) for more help.
