# Audio

MLOOP supports multiple audio output options through mpv and ALSA/PipeWire.

## Audio Output Options

| Option | Description |
|--------|-------------|
| `auto` | Automatic detection (default) |
| `hdmi` | HDMI audio output |
| `system-default` | System default audio output |

With the mpv backend, these map to mpv's `audio-device` property. `auto` and `system-default`
use mpv automatic selection, while `hdmi` maps to the configured HDMI ALSA output alias.

## Configuration

Set the audio output in `/etc/mloop/config.toml`:

```toml
[audio]
output = "auto"
```

## Changing Audio Output

Use the HDMI gesture menu to change audio output:

1. Enter the menu (unplug HDMI for 1-8 seconds, then replug)
2. Navigate to "Audio output"
3. Stay connected for 5 seconds to select
4. Navigate through available options
5. Stay connected to confirm

The selected audio output is saved in `/var/lib/mloop/state.toml` and reused after restart.

## Troubleshooting

### No Audio

1. Check that the display supports HDMI audio
2. Verify audio output configuration
3. Check ALSA/PipeWire status:
   ```bash
   aplay -l
   wpctl status
   ```
4. Check MLOOP logs for audio errors

### Audio Does Not Recover After HDMI Reconnect

This is a known issue on some displays. Try:

1. Using `hdmi` audio output explicitly
2. Checking display settings for audio output
3. Rebooting the device
