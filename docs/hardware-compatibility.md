# Hardware Compatibility

This document tracks tested hardware configurations for MLOOP.

## Test Matrix

| Pi Model | OS Version | Display | HDMI Port | Audio | Gestures | Notes |
|----------|------------|---------|-----------|-------|----------|-------|
| - | - | - | - | - | - | Awaiting testing |

## How to Report

To report hardware compatibility results:

1. Run `scripts/collect-debug-info.sh` on your device
2. Create a [Hardware Compatibility Report](https://github.com/yourusername/mloop/issues/new?template=hardware_report.yml)
3. Include test results and any issues encountered

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
