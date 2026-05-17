# Troubleshooting

Common issues and solutions for MLOOP.

## No Video Output

1. **Check HDMI connection** - Ensure the cable is securely connected
2. **Check display power** - Ensure the display is powered on
3. **Check connector status**:
   ```bash
   cat /sys/class/drm/card*-HDMI-A-*/status
   ```
   Should show `connected`
4. **Check MLOOP service**:
   ```bash
   sudo systemctl status mloop
   ```
5. **Check logs**:
   ```bash
   sudo journalctl -u mloop -n 100
   ```

## No Audio

1. **Check audio output configuration** in `/etc/mloop/config.toml`
2. **List available audio devices**:
   ```bash
   aplay -l
   ```
3. **Check PipeWire status**:
   ```bash
   wpctl status
   ```
4. **Try different audio output** via HDMI gesture menu

## HDMI Menu Does Not Trigger

1. **Check that gestures are enabled**:
   ```toml
   [hdmi_gestures]
   enabled = true
   ```
2. **Verify HDMI detection is working**:
   ```bash
   cat /sys/class/drm/card*-HDMI-A-*/status
   ```
3. **Try adjusting timing values** - Your display may have different detection timing
4. **Check for forced HDMI mode** - This may disable hotplug detection

## Display Goes Black After Boot

1. **Check for media files** in configured directories
2. **Verify mpv is installed**:
   ```bash
   mpv --version
   ```
3. **Check logs for errors**

## mpv Fails to Start

1. **Verify mpv installation**:
   ```bash
   which mpv
   mpv --version
   ```
2. **Check mpv path in configuration**:
   ```toml
   [player]
   mpv_path = "/usr/bin/mpv"
   ```
3. **Check IPC socket directory exists**:
   ```bash
   ls -la /run/mloop/
   ```

## Media Not Detected

1. **Check media directory configuration**:
   ```toml
   [playback]
   media_dirs = ["/home/mloop/media"]
   ```
2. **Verify files exist and have correct permissions**:
   ```bash
   ls -la /home/mloop/media/
   ```
3. **Check file extensions** - Only supported formats are scanned
4. **Rescan media** via HDMI gesture menu

## Collecting Logs

Use the debug collection script:

```bash
./scripts/collect-debug-info.sh
```

This collects:
- System information
- MLOOP service status
- Recent logs
- DRM connector status
- Audio device information
- Player version information

Include this output when reporting issues.
