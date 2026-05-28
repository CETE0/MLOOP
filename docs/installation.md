# Installation

This guide covers installing MLOOP on a Raspberry Pi. For development setup on any OS, see [development.md](development.md).

## Prerequisites

- Raspberry Pi 3, 4, or 5
- Raspberry Pi OS Lite Bookworm or newer
- HDMI display
- Storage for media files

## Step 1: Install Raspberry Pi OS Lite

1. Download Raspberry Pi OS Lite (Bookworm) from the [official website](https://www.raspberrypi.com/software/)
2. Flash the image to your SD card using Raspberry Pi Imager
3. Boot the Pi and complete initial setup

## Step 2: Install MLOOP

Clone the repository and run the install script:

```bash
git clone https://github.com/CETE0/mloop.git
cd mloop
sudo packaging/install.sh
```

The install script handles everything automatically:
- Installs system dependencies (mpv, python3, pip, venv)
- Creates the `mloop` system user
- Creates required directories (`/etc/mloop`, `/var/lib/mloop`, `/run/mloop`, `/home/mloop/media`, `/opt/mloop`)
- Copies the MLOOP source to `/opt/mloop/src` and installs it in a virtual environment at `/opt/mloop/venv`
- Installs the default configuration
- Enables and starts the systemd service

> **Note:** The checkout directory can be removed after installation. MLOOP runs entirely from `/opt/mloop`.

## Alternative: Build a Flashable Image

Instead of installing on an existing Pi OS, you can build a pre-configured Raspberry Pi OS image with MLOOP baked in:

```bash
./packaging/image/build-pi-image.sh
```

Requires a Debian/Ubuntu host with Docker. Output is a `.img.xz` under `build/pi-gen/deploy/`. Flash with Raspberry Pi Imager or `dd`.

See [packaging/image/README.md](../packaging/image/README.md) for details.

## Step 3: Configure MLOOP (optional)

The default configuration is installed at `/etc/mloop/config.toml`. Edit it if needed:

```bash
sudo nano /etc/mloop/config.toml
```

## Step 4: Add Media

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

## Updating MLOOP

To update, pull the latest source and re-run the install script:

```bash
cd /path/to/mloop-checkout
git pull
sudo packaging/install.sh
```

## Troubleshooting

If MLOOP doesn't start:

1. Check that mpv is installed: `mpv --version`
2. Check that media files exist in the configured directory
3. Check logs: `sudo journalctl -u mloop -n 100`

See [Troubleshooting](troubleshooting.md) for more help.
