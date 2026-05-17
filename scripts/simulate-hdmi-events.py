#!/usr/bin/env python3
"""Simulate HDMI events for testing MLOOP gesture state machine."""

from __future__ import annotations

import sys
import time
from pathlib import Path


def simulate_events(
    sysfs_path: Path,
    events: list[tuple[str, float]],
) -> None:
    """Simulate HDMI connect/disconnect events.

    Args:
        sysfs_path: Path to the connector status file.
        events: List of (state, delay) tuples.
    """
    for state, delay in events:
        print(f"Setting HDMI state to: {state}")
        sysfs_path.write_text(state + "\n")
        time.sleep(delay)


def main() -> None:
    """Run HDMI event simulation."""
    if len(sys.argv) < 2:
        print("Usage: simulate-hdmi-events.py <sysfs_status_path> [scenario]")
        print("Scenarios: enter_menu, navigate, select")
        sys.exit(1)

    status_path = Path(sys.argv[1])
    scenario = sys.argv[2] if len(sys.argv) > 2 else "enter_menu"

    if not status_path.exists():
        print(f"Error: {status_path} does not exist")
        sys.exit(1)

    scenarios = {
        "enter_menu": [
            ("disconnected", 2.0),
            ("connected", 0.5),
        ],
        "navigate": [
            ("disconnected", 0.5),
            ("connected", 0.5),
            ("disconnected", 0.5),
            ("connected", 0.5),
        ],
        "select": [
            ("disconnected", 2.0),
            ("connected", 6.0),
        ],
    }

    if scenario not in scenarios:
        print(f"Unknown scenario: {scenario}")
        print(f"Available: {', '.join(scenarios.keys())}")
        sys.exit(1)

    print(f"Simulating scenario: {scenario}")
    print(f"Status file: {status_path}")
    print()

    simulate_events(status_path, scenarios[scenario])

    print()
    print("Simulation complete")


if __name__ == "__main__":
    main()
