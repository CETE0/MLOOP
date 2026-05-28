# Development

This guide covers setting up a development environment for MLOOP.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mloop.git
   cd mloop
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install in editable mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Running MLOOP

### Development Mode (any OS)

Use the dev-run script to run MLOOP without installing as a system service:

```bash
./scripts/dev-run.sh
```

This uses a development config at `/tmp/mloop/config.toml` with paths safe for macOS/Linux development.

**Requirements:** `mpv` must be installed. On macOS: `brew install mpv`. On Debian/Ubuntu: `sudo apt install mpv`.

**Custom config:** Set `MLOOP_CONFIG_DIR` to use a different config directory:

```bash
export MLOOP_CONFIG_DIR="/path/to/config"
python -m mloop
```

### Production Mode (Raspberry Pi)

On a Raspberry Pi with MLOOP installed via `packaging/install.sh`, the daemon runs as a systemd service:

```bash
sudo systemctl status mloop
sudo journalctl -u mloop -f
```

## Code Structure

```
src/mloop/
├── __init__.py      # Package initialization
├── __main__.py      # Entry point
├── daemon.py        # Main daemon logic
├── config.py        # Configuration loading
├── logging.py       # Logging setup
├── media.py         # Media scanning and playlist
├── player/          # Playback backend
│   ├── mpv.py       # mpv controller
│   └── ipc.py       # mpv JSON IPC client
├── display/         # Display management
│   ├── drm.py       # DRM connector discovery
│   ├── hdmi_watcher.py  # HDMI state monitoring
│   └── rotation.py  # Video rotation
├── gestures/        # HDMI gesture detection
│   ├── state_machine.py  # Gesture state machine
│   └── events.py    # Event definitions
├── menu/            # Configuration menu
│   ├── model.py     # Menu data model
│   ├── controller.py    # Menu controller
│   └── actions.py   # Menu actions
├── audio/           # Audio management
│   └── devices.py   # Audio device detection
└── system/          # System integration
    ├── service.py   # Service management
    └── platform.py  # Platform detection
```

## Testing

### Automated Tests (any OS)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mloop

# Run specific test file
pytest tests/unit/test_config.py

# Run with verbose output
pytest -v
```

The suite includes 64 tests (unit + integration) covering:
- Config loading and defaults
- Media scanning and playlist building
- HDMI gesture state machine
- mpv IPC client behavior
- Menu model/controller/actions
- Player backend factory
- Fake sysfs HDMI watcher simulation

### Integration Tests

Integration tests use fake sysfs directories to simulate HDMI events:

```
tests/fixtures/sysfs_connected/
tests/fixtures/sysfs_disconnected/
```

### Hardware Validation (Raspberry Pi only)

For real-device testing, use the validation script:

```bash
./scripts/validate-player.sh /path/to/test-video.mp4
```

This compares mpv vs cvlc playback, measures CPU usage, and tests HDMI unplug/replug recovery. Generates a markdown report.

To collect system debug info:

```bash
./scripts/collect-debug-info.sh
```

Document results in `docs/hardware-compatibility.md`.

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check for lint errors
ruff check .

# Format code
ruff format .
```

All code must pass linting and formatting checks before merging.

## Adding New Features

1. Create a feature branch
2. Implement the feature
3. Add tests
4. Update documentation
5. Submit a pull request

## Hardware Testing

When testing on real hardware:

1. Run `scripts/collect-debug-info.sh` to gather system information
2. Document results in `docs/hardware-compatibility.md`
3. Report any issues or anomalies
