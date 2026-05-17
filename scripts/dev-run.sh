#!/usr/bin/env bash
set -euo pipefail

# MLOOP Development Run Script
# Runs MLOOP in development mode without installing as a service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -e ".[dev]"
fi

# Activate virtual environment
source .venv/bin/activate

# Create runtime directories
mkdir -p /tmp/mloop/run
mkdir -p /tmp/mloop/state
mkdir -p /tmp/mloop/logs

echo "Starting MLOOP in development mode..."
echo "Press Ctrl+C to stop"

# Run with development config
export MLOOP_CONFIG_DIR="/tmp/mloop"
python -m mloop "$@"
