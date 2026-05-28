# MLOOP Raspberry Pi OS Image

This folder contains a reproducible image-build scaffold for Raspberry Pi OS
Lite using `pi-gen`.

Use this when you want a flashable image with MLOOP already installed,
configured, and enabled as a systemd service.

## Requirements

Build on a Debian/Ubuntu Linux host or VM with Docker available.

```bash
sudo apt-get update
sudo apt-get install -y git docker.io rsync xz-utils
sudo usermod -aG docker "$USER"
```

Log out and back in after adding your user to the `docker` group.

## Build

From the MLOOP repository root:

```bash
./packaging/image/build-pi-image.sh
```

The script clones `pi-gen` into `build/pi-gen`, copies this checkout into a
custom `stage-mloop`, and runs `pi-gen` with a minimal Raspberry Pi OS Lite
configuration.

The image output will be under:

```text
build/pi-gen/deploy/
```

Flash the resulting `.img.xz` with Raspberry Pi Imager, Balena Etcher, or `dd`.

## Defaults

The image contains:

- Raspberry Pi OS Lite
- `mpv`, `cvlc`, `python3`, `python3-pip`, `python3-venv`
- MLOOP installed into `/opt/mloop/venv`
- source copied into `/opt/mloop/src`
- config at `/etc/mloop/config.toml`
- media directory at `/home/mloop/media`
- enabled `mloop.service`

The service starts automatically on boot. Add media files to
`/home/mloop/media` after flashing, or place files in
`packaging/image/stage-mloop/00-install-mloop/files/media/` before building if
you want media baked into the image.

## Important

This produces an alpha test image. Real HDMI gesture behavior still needs to be
validated on the exact Raspberry Pi, display, cable, and video mode used in the
installation.
