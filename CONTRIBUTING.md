# Contributing to MLOOP

Thank you for your interest in contributing to MLOOP! This document provides guidelines and instructions for contributing.

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

## Branch Naming

- `feature/description` for new features
- `fix/description` for bug fixes
- `docs/description` for documentation changes
- `test/description` for test additions or changes

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mloop

# Run specific test file
pytest tests/unit/test_config.py
```

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check for lint errors
ruff check .

# Format code
ruff format .
```

All code must pass `ruff check` and `ruff format --check` before merging.

## Adding Hardware Compatibility Data

When testing on new hardware:

1. Run `scripts/collect-debug-info.sh` on the target device
2. Add results to `docs/hardware-compatibility.md`
3. Note any issues or anomalies in the compatibility table

## Writing Documentation

- Keep documentation clear and accessible to non-developers
- Use markdown formatting
- Include code examples where helpful
- Update relevant docs when changing functionality

## Pull Requests

- Reference related issues in the PR description
- Include test coverage for new functionality
- Update documentation as needed
- Keep changes focused and atomic
- Follow the existing code style

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.
