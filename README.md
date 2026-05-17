# MLOOP

MLOOP is an open-source Raspberry Pi video looper for galleries, museums, exhibitions, and kiosk installations. It boots directly into fullscreen media playback and provides a no-keyboard configuration mode controlled through HDMI unplug/replug gestures.

## Project Status

**Experimental prototype.** MLOOP is being developed for Raspberry Pi OS Lite Bookworm and modern KMS/DRM systems. HDMI gesture control depends on display, cable, Raspberry Pi model, and video mode configuration. Please see the hardware compatibility table before using in production installations.

## Features

- Automatic fullscreen playback on boot
- Media folder scanning with playlist generation
- HDMI hotplug detection and gesture-based menu
- mpv playback backend with JSON IPC control
- Persistent configuration via TOML files
- systemd service integration
- No keyboard or network required

## Hardware Requirements

- Raspberry Pi 3, 4, or 5
- Raspberry Pi OS Lite Bookworm or newer
- HDMI display
- Storage for media files

## Quick Install

```bash
# Clone the repository
git clone https://github.com/CETE0/MLOOP.git
cd mloop

# Install in editable mode
pip install -e .

# Run the daemon
mloopd
```

For a full installation guide, see [docs/installation.md](docs/installation.md).

## HDMI Gesture Control

MLOOP uses HDMI unplug/replug gestures for configuration without a keyboard:

| Gesture | Action |
|---------|--------|
| Unplug 1-8s, replug | Enter configuration menu |
| Quick unplug/replug | Navigate to next menu item |
| Stay connected 5s | Select highlighted item |
| No activity 30s | Exit menu, resume playback |

See [docs/hdmi-gestures.md](docs/hdmi-gestures.md) for full documentation.

## Configuration

Configuration files:

- `/etc/mloop/config.toml` - User-editable configuration
- `/var/lib/mloop/state.toml` - Runtime state
- `/run/mloop/mpv.sock` - mpv IPC socket

See [docs/configuration.md](docs/configuration.md) for all options.

## Documentation

- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [HDMI Gestures](docs/hdmi-gestures.md)
- [Media](docs/media.md)
- [Audio](docs/audio.md)
- [Display](docs/display.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Hardware Compatibility](docs/hardware-compatibility.md)
- [Development](docs/development.md)

## Limitations

- HDMI gesture control is experimental and may not work with all displays or configurations
- Forced HDMI output mode may interfere with hotplug detection
- mpv playback must be validated against cvlc on target hardware

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) for details.
