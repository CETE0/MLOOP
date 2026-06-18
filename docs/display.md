# Display

MLOOP uses the Linux DRM/KMS graphics stack for display output.

## Display Configuration

```toml
[display]
connector = "auto"
rotation = 0
mode = "auto"
```

## Connector Auto-Detection

By default, MLOOP auto-detects the HDMI connector. You can override this:

```toml
[display]
connector = "HDMI-A-1"
```

Common connector names:

- `HDMI-A-1` - First HDMI port
- `HDMI-A-2` - Second HDMI port (Pi 4/5)

## Video Rotation

Supported rotation values:

- `0` - No rotation (default)
- `90` - 90 degrees clockwise
- `180` - 180 degrees
- `270` - 270 degrees clockwise (90 counter-clockwise)

Change rotation via the HDMI gesture menu or configuration file.

## Display Modes

By default, MLOOP uses the display's preferred mode. Runtime mode switching through
`display.mode` is not implemented; the only accepted value is `auto`.

## Forced HDMI Output

For kiosk installations, you may want to force HDMI output even when no display is connected. This is done via kernel command line options in `/boot/firmware/cmdline.txt`:

```
video=HDMI-A-1:1280x720@60D
```

**Warning:** Forced HDMI mode may interfere with hotplug detection. See [HDMI Gestures](hdmi-gestures.md) for details.

## EDID Firmware

You can provide a custom EDID file:

```
drm.edid_firmware=HDMI-A-1:myedid.dat
```

Place the EDID file in `/lib/firmware/`.

## Troubleshooting

### No Display Output

1. Check HDMI cable connection
2. Verify display is powered on
3. Check connector status: `cat /sys/class/drm/card*-HDMI-A-*/status`
4. Check MLOOP logs

### Display Goes Black After Boot

1. Check that media files exist
2. Verify mpv is installed and working
3. Check for errors in logs

### Wrong Resolution

1. Check display EDID: `cat /sys/class/drm/card*-HDMI-A-*/edid`
2. Force a specific mode with kernel DRM/KMS options
3. Check display settings
