# Hardware Compatibility

This document tracks tested hardware configurations for MLOOP.

## Player Backend Comparison

MLOOP supports two player backends: **mpv** (default) and **cvlc** (VLC CLI fallback).
The table below records real-hardware comparison results. Run `scripts/validate-player.sh`
on your Raspberry Pi to populate a new row.

### Comparison Matrix

| Pi Model | OS | Display | Codec | Backend | Avg CPU% | Stutter? | Loop Gap | HDMI Recovery | Audio Recovery | Verdict |
|----------|----|---------|-------|---------|----------|----------|-----------|---------------|----------------|---------|
| Pi 4 | Bookworm | - | H.264 | mpv | - | - | - | - | - | Awaiting test |
| Pi 4 | Bookworm | - | H.264 | cvlc | - | - | - | - | - | Awaiting test |
| Pi 4 | Bookworm | - | H.265 | mpv | - | - | - | - | - | Awaiting test |
| Pi 4 | Bookworm | - | H.265 | cvlc | - | - | - | - | - | Awaiting test |
| Pi 5 | Bookworm | - | H.264 | mpv | - | - | - | - | - | Awaiting test |
| Pi 5 | Bookworm | - | H.264 | cvlc | - | - | - | - | - | Awaiting test |
| Pi 5 | Bookworm | - | H.265 | mpv | - | - | - | - | - | Awaiting test |
| Pi 5 | Bookworm | - | H.265 | cvlc | - | - | - | - | - | Awaiting test |
| Pi 3 | Bookworm | - | H.264 | mpv | - | - | - | - | - | Awaiting test |
| Pi 3 | Bookworm | - | H.264 | cvlc | - | - | - | - | - | Awaiting test |

### Backend Feature Matrix

| Feature | mpv | cvlc |
|---------|-----|------|
| Fullscreen playback | Yes | Yes |
| Infinite loop | Yes | Yes |
| JSON IPC (runtime control) | Yes | No |
| OSD overlay (show_text) | Yes | Stub |
| Runtime volume control | Yes | Stub |
| Runtime rotation | Yes | Stub |
| Runtime audio device switch | Yes | Stub |
| Playlist management | Yes | File args only |
| Process supervision | Yes | Yes |
| Config-driven backend selection | Yes | Yes |

**Recommendation:** Use mpv as the primary backend. cvlc is available as a
fallback for hardware where mpv underperforms, but interactive features
(menu, OSD, volume/rotation changes) will be limited.

## Test Matrix

| Pi Model | OS Version | Display | HDMI Port | Audio | Gestures | Notes |
|----------|------------|---------|-----------|-------|----------|-------|
| - | - | - | - | - | - | Awaiting testing |

## How to Run Validation

```bash
# On a Raspberry Pi with a test video file
./scripts/validate-player.sh --output /tmp/mloop-results /path/to/test-video.mp4
```

The script will:
1. Collect system information (Pi model, OS, DRM connectors, HDMI status)
2. Play the test file with **mpv** for the configured duration, recording CPU usage
3. Play the test file with **cvlc** for the configured duration, recording CPU usage
4. Guide you through an interactive **HDMI disconnect/reconnect recovery test**
5. Output a structured Markdown report at the specified output path

Copy the generated report into this document's comparison matrix above.

## How to Report

To report hardware compatibility results:

1. Run `scripts/validate-player.sh` on your device
2. Run `scripts/collect-debug-info.sh` to collect system information
3. Create a [Hardware Compatibility Report](https://github.com/CETE0/MLOOP/issues/new?template=hardware_report.yml)
4. Include test results and any issues encountered

## Required Information

For each test, please provide:

- Raspberry Pi model and OS image date/version
- Display model and physical HDMI port used
- `kmsprint | grep Connector` output
- `/sys/class/drm/*/status` before, during, and after disconnect
- Player backend tested (mpv and/or cvlc)
- Whether video resumes after reconnect
- Whether HDMI audio resumes after reconnect
- Whether forced output mode changes hotplug behavior
- Observed reconnect-to-visible-image delay
- Whether staff can perform gestures without precise timing

## Known Issues

### Raspberry Pi 3

- Limited hardware decode support
- Higher CPU usage for video playback
- Consider using cvlc instead of mpv

### Raspberry Pi 4

- Two HDMI ports (HDMI-A-1 and HDMI-A-2)
- HDMI-A-1 is primary, HDMI-A-2 may have different behavior
- Hardware decode available for H.264

### Raspberry Pi 5

- Similar to Pi 4 but with improved performance
- Newer kernel may have different DRM behavior

## Forced HDMI Mode

When using forced HDMI output mode:

- Playback may be more reliable
- HDMI gesture detection may not work
- Consider using alternative configuration methods

## Display Compatibility

Some displays may have:

- Slow EDID detection
- Non-standard hotplug behavior
- No HDMI audio support

Test your specific display and report results.
