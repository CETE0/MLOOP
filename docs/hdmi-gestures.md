# HDMI Gestures

MLOOP uses HDMI unplug/replug gestures for configuration without a keyboard or network connection.

## How It Works

The HDMI gesture system detects physical HDMI cable disconnections and reconnections through the Linux DRM/KMS connector status interface.

## Gesture Timing

| Gesture | Timing | Action |
|---------|--------|--------|
| Enter menu | Unplug 1-8 seconds, then replug | Opens configuration menu |
| Navigate | Quick unplug/replug (0.3-5s) | Moves to next menu item |
| Select | Stay connected for 5 seconds | Selects highlighted item |
| Exit | No activity for 30 seconds | Closes menu, resumes playback |

## Configuration Menu

When the menu is open, you will see options displayed on screen using mpv's OSD:

1. **Resume playback** - Exit menu and continue playback
2. **Volume** - Adjust volume level
3. **Audio output** - Switch audio output device
4. **Rotate video** - Change video rotation
5. **Rescan media** - Rescan media directories
6. **Show network info** - Display network configuration
7. **Reboot** - Reboot the device (requires confirmation)
8. **Shutdown** - Shut down the device (requires confirmation)

## Timing Configuration

All timing values can be adjusted in the configuration file:

```toml
[hdmi_gestures]
enter_min_disconnect_ms = 800
enter_max_disconnect_ms = 8000
cycle_min_disconnect_ms = 300
cycle_max_disconnect_ms = 5000
debounce_ms = 100
select_after_connected_ms = 5000
menu_timeout_ms = 30000
```

`debounce_ms` must be lower than `cycle_min_disconnect_ms`. If a display or cable produces noisy
hotplug transitions, increase debounce carefully while keeping enough room for 300 ms navigation
gestures.

## Compatibility

HDMI gesture control depends on:

- Raspberry Pi model (Pi 3, 4, 5)
- Display model and EDID support
- Cable quality and length
- HDMI port used (HDMI-A-1 vs HDMI-A-2)
- Display mode configuration

### Forced HDMI Mode

If you have forced HDMI output mode enabled (via kernel command line options like `video=HDMI-A-1:1280x720@60D` or EDID firmware), hotplug detection may not work correctly.

MLOOP supports two modes:

- **Auto HDMI mode**: HDMI gestures work normally
- **Forced output mode**: Playback may be more reliable, but HDMI gestures may be unavailable

See [Display Configuration](display.md) for more information.

## Troubleshooting

### Menu does not trigger

1. Check that HDMI gestures are enabled in config: `enabled = true`
2. Verify the HDMI cable is being detected: `cat /sys/class/drm/card*-HDMI-A-*/status`
3. Try adjusting timing values in the configuration
4. Check logs: `sudo journalctl -u mloop -f`

### Gestures are too sensitive or not sensitive enough

Adjust the timing values in `[hdmi_gestures]` section of the configuration file.
Keep `debounce_ms` below `cycle_min_disconnect_ms`; the default is 100 ms.
