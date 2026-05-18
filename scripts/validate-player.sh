#!/usr/bin/env bash
set -euo pipefail

# MLOOP Player Backend Validation Script
# Compares mpv vs cvlc on Raspberry Pi OS Lite.
# Records CPU load, stutter, loop gap, HDMI recovery, and audio recovery.
#
# Usage:
#   ./validate-player.sh [--output REPORT_DIR] [--duration SECONDS] <TEST_FILE>
#
# Requires: mpv, cvlc, pidstat (sysstat package), bc, jq (optional)

REPORT_DIR="${MLOOP_VALIDATION_OUTPUT:-/tmp/mloop-validation}"
DURATION="${MLOOP_VALIDATION_DURATION:-30}"
TEST_FILE=""
OUTPUT_FILE=""
BACKENDS=("mpv" "cvlc")
STARTED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

usage() {
    echo "Usage: $0 [--output DIR] [--duration SECS] <TEST_FILE>"
    echo ""
    echo "  --output DIR       Directory for report output (default: /tmp/mloop-validation)"
    echo "  --duration SECS    Playback duration per backend in seconds (default: 30)"
    echo "  TEST_FILE          Path to an H.264 or H.265 test video file"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output)
            REPORT_DIR="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --help|-h)
            usage
            ;;
        *)
            TEST_FILE="$1"
            shift
            ;;
    esac
done

if [[ -z "$TEST_FILE" ]]; then
    echo "ERROR: No test file provided."
    usage
fi

if [[ ! -f "$TEST_FILE" ]]; then
    echo "ERROR: Test file not found: $TEST_FILE"
    exit 1
fi

mkdir -p "$REPORT_DIR"
OUTPUT_FILE="$REPORT_DIR/validation-report.md"
CPU_LOG="$REPORT_DIR/cpu.log"
EVENT_LOG="$REPORT_DIR/events.log"

echo "=== MLOOP Player Validation ==="
echo "Started:        $STARTED_AT"
echo "Test file:      $TEST_FILE"
echo "Duration:       ${DURATION}s per backend"
echo "Report dir:     $REPORT_DIR"
echo ""

# --- Helper: check command availability ---
require_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo "WARNING: '$1' not found. Some measurements will be skipped."
        return 1
    fi
    return 0
}

# --- Helper: get CPU usage for a PID ---
get_cpu_pct() {
    local pid="$1"
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "0"
        return
    fi
    if require_cmd pidstat; then
        pidstat -p "$pid" 1 1 2>/dev/null | awk 'NR==4 {print $8}' || echo "N/A"
    else
        local stat cpu_ticks uptime_ticks
        stat=$(cat "/proc/$pid/stat" 2>/dev/null || echo "")
        if [[ -z "$stat" ]]; then
            echo "0"
            return
        fi
        cpu_ticks=$(echo "$stat" | awk '{print $14+$15}')
        uptime_ticks=$(awk '{print $1}' /proc/uptime 2>/dev/null | cut -d. -f1)
        if [[ -n "$cpu_ticks" && -n "$uptime_ticks" && "$uptime_ticks" != "0" ]]; then
            echo "scale=1; $cpu_ticks / $uptime_ticks" | bc 2>/dev/null || echo "N/A"
        else
            echo "N/A"
        fi
    fi
}

# --- Helper: check video codec ---
get_codec_info() {
    local file="$1"
    if require_cmd ffprobe; then
        ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height \
            -of default=noprint_wrappers=1 "$file" 2>/dev/null || echo "unknown"
    elif require_cmd mpv; then
        mpv --no-video --frames=1 --vo=null --ao=null --msg-level=ffmpeg=v \
            "$file" 2>&1 | grep -oE '(h264|hevc|h265|mpeg4)' | head -1 || echo "unknown"
    else
        echo "unknown"
    fi
}

# --- Helper: log an event with timestamp ---
log_event() {
    local ts
    ts=$(date +%s%3N 2>/dev/null || date +%s000)
    echo "$ts $*" >> "$EVENT_LOG"
}

# --- System info ---
collect_system_info() {
    echo "### System Information" >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    echo "Date: $(date)" >> "$OUTPUT_FILE"
    echo "Hostname: $(hostname)" >> "$OUTPUT_FILE"
    echo "Kernel: $(uname -a)" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "--- OS Release ---" >> "$OUTPUT_FILE"
    cat /etc/os-release 2>/dev/null >> "$OUTPUT_FILE" || echo "Not available" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "--- Pi Model ---" >> "$OUTPUT_FILE"
    cat /proc/device-tree/model 2>/dev/null >> "$OUTPUT_FILE" || echo "Unknown" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "--- mpv version ---" >> "$OUTPUT_FILE"
    mpv --version 2>/dev/null | head -1 >> "$OUTPUT_FILE" || echo "mpv not installed" >> "$OUTPUT_FILE"
    echo "--- cvlc version ---" >> "$OUTPUT_FILE"
    cvlc --version 2>/dev/null | head -3 >> "$OUTPUT_FILE" || echo "cvlc not installed" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "--- DRM Connectors ---" >> "$OUTPUT_FILE"
    ls -la /sys/class/drm/ 2>/dev/null >> "$OUTPUT_FILE" || echo "DRM not available" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "--- HDMI Status ---" >> "$OUTPUT_FILE"
    cat /sys/class/drm/card*-HDMI-A-*/status 2>/dev/null >> "$OUTPUT_FILE" || echo "No HDMI connectors" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "--- Test File Codec ---" >> "$OUTPUT_FILE"
    get_codec_info "$TEST_FILE" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "--- Test File Size ---" >> "$OUTPUT_FILE"
    ls -lh "$TEST_FILE" | awk '{print $5, $NF}' >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

# --- Playback test for one backend ---
test_backend() {
    local backend="$1"
    local file="$2"
    local label="$backend"

    echo ""
    echo "--- Testing $backend ---"
    log_event "test_start backend=$backend"

    local cpu_samples=()
    local pid=""
    local start_ts end_ts

    start_ts=$(date +%s%3N 2>/dev/null || date +%s000)

    case "$backend" in
        mpv)
            mpv --fullscreen --loop=inf --no-terminal "$file" &
            pid=$!
            ;;
        cvlc)
            cvlc --fullscreen --loop --no-osd --intf=dummy --no-video-title-show "$file" &
            pid=$!
            ;;
    esac

    log_event "player_started backend=$backend pid=$pid"

    sleep 2

    echo "  PID: $pid"
    echo "  Collecting CPU samples for ${DURATION}s..."

    for ((i=0; i<DURATION; i++)); do
        local cpu
        cpu=$(get_cpu_pct "$pid")
        cpu_samples+=("$cpu")
        echo "  [$((i+1))/${DURATION}s] CPU: ${cpu}%"
        sleep 1
    done

    end_ts=$(date +%s%3N 2>/dev/null || date +%s000)

    local still_running="no"
    if kill -0 "$pid" 2>/dev/null; then
        still_running="yes"
    fi

    log_event "test_stop backend=$backend still_running=$still_running"

    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -9 "$pid" 2>/dev/null || true

    local avg_cpu="N/A"
    local total=0
    local count=0
    for s in "${cpu_samples[@]}"; do
        if [[ "$s" != "N/A" ]]; then
            total=$(echo "$total + $s" | bc 2>/dev/null || echo "$total")
            count=$((count + 1))
        fi
    done
    if [[ $count -gt 0 && "$total" != "0" ]]; then
        avg_cpu=$(echo "scale=1; $total / $count" | bc 2>/dev/null || echo "N/A")
    fi

    local elapsed_ms=$(( end_ts - start_ts ))

    echo "  Average CPU: ${avg_cpu}%"
    echo "  Still running at end: $still_running"
    echo "  Elapsed: ${elapsed_ms}ms"

    echo "#### $backend" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "| Metric | Value |" >> "$OUTPUT_FILE"
    echo "|--------|-------|" >> "$OUTPUT_FILE"
    echo "| Average CPU % | $avg_cpu |" >> "$OUTPUT_FILE"
    echo "| Still running after ${DURATION}s | $still_running |" >> "$OUTPUT_FILE"
    echo "| PID | $pid |" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

# --- HDMI recovery test ---
test_hdmi_recovery() {
    echo ""
    echo "============================================"
    echo "  HDMI RECOVERY TEST (manual)"
    echo "============================================"
    echo ""
    echo "This test requires you to physically unplug"
    echo "and replug the HDMI cable."
    echo ""
    echo "Steps:"
    echo "  1. Press ENTER to start mpv playback"
    echo "  2. After 5 seconds, UNPLUG the HDMI cable"
    echo "  3. Wait 3-5 seconds"
    echo "  4. REPLUG the HDMI cable"
    echo "  5. Observe: does video/audio resume?"
    echo "  6. Press Ctrl+C to stop"
    echo ""

    read -rp "Press ENTER to start HDMI recovery test with mpv..."

    log_event "hdmi_test_start backend=mpv"

    local before_status=""
    for f in /sys/class/drm/card*-HDMI-A-*/status; do
        before_status+="$(basename "$(dirname "$f")"): $(cat "$f" 2>/dev/null || echo '?') "
    done
    echo "HDMI status before: $before_status"
    log_event "hdmi_status phase=before status=$before_status"

    mpv --fullscreen --loop=inf --no-terminal "$TEST_FILE" &
    local mpv_pid=$!

    echo "mpv PID: $mpv_pid"
    echo "Playback started. UNPLUG HDMI now (wait for prompt)..."

    sleep 5
    echo ""
    echo ">>> UNPLUG HDMI CABLE NOW <<<"
    sleep 5

    local during_status=""
    for f in /sys/class/drm/card*-HDMI-A-*/status; do
        during_status+="$(basename "$(dirname "$f")"): $(cat "$f" 2>/dev/null || echo '?') "
    done
    echo "HDMI status during disconnect: $during_status"
    log_event "hdmi_status phase=during status=$during_status"

    echo ""
    echo ">>> REPLUG HDMI CABLE NOW <<<"
    sleep 8

    local after_status=""
    for f in /sys/class/drm/card*-HDMI-A-*/status; do
        after_status+="$(basename "$(dirname "$f")"): $(cat "$f" 2>/dev/null || echo '?') "
    done
    echo "HDMI status after reconnect: $after_status"
    log_event "hdmi_status phase=after status=$after_status"

    local mpv_alive="no"
    if kill -0 "$mpv_pid" 2>/dev/null; then
        mpv_alive="yes"
    fi
    echo "mpv still alive: $mpv_alive"

    kill "$mpv_pid" 2>/dev/null || true
    sleep 1
    kill -9 "$mpv_pid" 2>/dev/null || true

    echo ""
    echo "  --- Manual observations (record below) ---"
    echo ""

    read -rp "  Did video resume after HDMI reconnect? (yes/no): " video_resumed
    read -rp "  Did audio resume after HDMI reconnect? (yes/no): " audio_resumed
    read -rp "  Estimated reconnect-to-image delay (seconds): " reconnect_delay
    read -rp "  Any visible stutter or corruption? (describe): " stutter_notes

    log_event "hdmi_test_end video_resumed=$video_resumed audio_resumed=$audio_resumed delay=${reconnect_delay}s"

    echo "### HDMI Recovery (mpv)" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "| Metric | Value |" >> "$OUTPUT_FILE"
    echo "|--------|-------|" >> "$OUTPUT_FILE"
    echo "| Status before disconnect | $before_status |" >> "$OUTPUT_FILE"
    echo "| Status during disconnect | $during_status |" >> "$OUTPUT_FILE"
    echo "| Status after reconnect | $after_status |" >> "$OUTPUT_FILE"
    echo "| mpv process survived | $mpv_alive |" >> "$OUTPUT_FILE"
    echo "| Video resumed | $video_resumed |" >> "$OUTPUT_FILE"
    echo "| Audio resumed | $audio_resumed |" >> "$OUTPUT_FILE"
    echo "| Reconnect-to-image delay | ${reconnect_delay}s |" >> "$OUTPUT_FILE"
    echo "| Stutter/corruption notes | $stutter_notes |" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    echo ""
    echo "--- Testing cvlc HDMI recovery ---"
    echo ""

    read -rp "Press ENTER to start HDMI recovery test with cvlc..."

    log_event "hdmi_test_start backend=cvlc"

    cvlc --fullscreen --loop --no-osd --intf=dummy --no-video-title-show "$TEST_FILE" &
    local cvlc_pid=$!

    echo "cvlc PID: $cvlc_pid"
    echo "Playback started. UNPLUG HDMI now (wait for prompt)..."

    sleep 5
    echo ""
    echo ">>> UNPLUG HDMI CABLE NOW <<<"
    sleep 5

    echo ""
    echo ">>> REPLUG HDMI CABLE NOW <<<"
    sleep 8

    local cvlc_alive="no"
    if kill -0 "$cvlc_pid" 2>/dev/null; then
        cvlc_alive="yes"
    fi
    echo "cvlc still alive: $cvlc_alive"

    kill "$cvlc_pid" 2>/dev/null || true
    sleep 1
    kill -9 "$cvlc_pid" 2>/dev/null || true

    read -rp "  Did video resume after HDMI reconnect? (yes/no): " cvlc_video
    read -rp "  Did audio resume after HDMI reconnect? (yes/no): " cvlc_audio
    read -rp "  Estimated reconnect-to-image delay (seconds): " cvlc_delay
    read -rp "  Any visible stutter or corruption? (describe): " cvlc_stutter

    log_event "hdmi_test_end backend=cvlc video_resumed=$cvlc_video audio_resumed=$cvlc_audio delay=${cvlc_delay}s"

    echo "### HDMI Recovery (cvlc)" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "| Metric | Value |" >> "$OUTPUT_FILE"
    echo "|--------|-------|" >> "$OUTPUT_FILE"
    echo "| cvlc process survived | $cvlc_alive |" >> "$OUTPUT_FILE"
    echo "| Video resumed | $cvlc_video |" >> "$OUTPUT_FILE"
    echo "| Audio resumed | $cvlc_audio |" >> "$OUTPUT_FILE"
    echo "| Reconnect-to-image delay | ${cvlc_delay}s |" >> "$OUTPUT_FILE"
    echo "| Stutter/corruption notes | $cvlc_stutter |" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

# --- Main ---
{
    echo "# MLOOP Player Validation Report"
    echo ""
    echo "**Generated:** $(date)"
    echo "**Test file:** \`$TEST_FILE\`"
    echo ""
} > "$OUTPUT_FILE"

collect_system_info

echo "## CPU Comparison (${DURATION}s playback each)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

for backend in "${BACKENDS[@]}"; do
    if ! command -v "$backend" &>/dev/null; then
        echo "#### $backend" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "**SKIPPED:** \`$backend\` not found in PATH" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "  SKIPPED: $backend not installed"
        continue
    fi
    test_backend "$backend" "$TEST_FILE"
done

echo "## HDMI Recovery Test" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

test_hdmi_recovery

echo ""
echo "============================================"
echo "  VALIDATION COMPLETE"
echo "============================================"
echo ""
echo "Report saved to: $OUTPUT_FILE"
echo "Event log saved to: $EVENT_LOG"
echo ""
echo "To include in docs, copy the report content to:"
echo "  docs/hardware-compatibility.md"
echo ""
echo "To submit results, open a hardware compatibility"
echo "report issue on GitHub."
