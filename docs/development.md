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

For development, use the dev-run script:

```bash
./scripts/dev-run.sh
```

This runs MLOOP without installing as a system service.

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

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mloop

# Run specific test file
pytest tests/unit/test_config.py
```

### Integration Tests

Integration tests use fake sysfs directories to simulate HDMI events:

```
tests/fixtures/sysfs_connected/
tests/fixtures/sysfs_disconnected/
```

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
