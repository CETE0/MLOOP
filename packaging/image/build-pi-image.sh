#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="${MLOOP_IMAGE_BUILD_DIR:-$PROJECT_ROOT/build}"
PI_GEN_DIR="${PI_GEN_DIR:-$BUILD_DIR/pi-gen}"
PI_GEN_REPO="${PI_GEN_REPO:-https://github.com/RPi-Distro/pi-gen.git}"
STAGE_NAME="stage-mloop"

if ! command -v git >/dev/null 2>&1; then
    echo "git is required" >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required to run pi-gen" >&2
    exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
    echo "rsync is required" >&2
    exit 1
fi

mkdir -p "$BUILD_DIR"

if [ ! -d "$PI_GEN_DIR/.git" ]; then
    git clone "$PI_GEN_REPO" "$PI_GEN_DIR"
else
    git -C "$PI_GEN_DIR" pull --ff-only
fi

rm -rf "$PI_GEN_DIR/$STAGE_NAME"
cp -R "$SCRIPT_DIR/$STAGE_NAME" "$PI_GEN_DIR/$STAGE_NAME"

rm -rf "$PI_GEN_DIR/$STAGE_NAME/00-install-mloop/files/mloop"
mkdir -p "$PI_GEN_DIR/$STAGE_NAME/00-install-mloop/files/mloop"

rsync -a \
    --exclude ".git/" \
    --exclude ".venv/" \
    --exclude "build/" \
    --exclude ".pytest_cache/" \
    --exclude ".ruff_cache/" \
    --exclude ".mypy_cache/" \
    "$PROJECT_ROOT/" "$PI_GEN_DIR/$STAGE_NAME/00-install-mloop/files/mloop/"

cat > "$PI_GEN_DIR/config" <<'EOF'
IMG_NAME="mloop-rpios-lite"
RELEASE="bookworm"
DEPLOY_ZIP=0
LOCALE_DEFAULT="en_US.UTF-8"
KEYBOARD_KEYMAP="us"
TIMEZONE_DEFAULT="UTC"
FIRST_USER_NAME="pi"
FIRST_USER_PASS="raspberry"
ENABLE_SSH=1
STAGE_LIST="stage0 stage1 stage2 stage-mloop"
EOF

echo "Starting pi-gen build in $PI_GEN_DIR"
echo "Output will be written to $PI_GEN_DIR/deploy"

cd "$PI_GEN_DIR"
./build-docker.sh
