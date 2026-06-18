# Configuration

MLOOP uses TOML configuration files. The main configuration file is located at `/etc/mloop/config.toml`.

## Configuration File Locations

- `/etc/mloop/config.toml` - User-editable configuration
- `/var/lib/mloop/state.toml` - Runtime state (modified by menu actions)
- `/run/mloop/mpv.sock` - mpv IPC socket (created at runtime)

## Example Configuration

```toml
[playback]
media_dirs = ["/home/mloop/media", "/media/mloop"]
shuffle = false
loop = true
volume = 80
image_duration_seconds = 10

[player]
backend = "mpv"
mpv_path = "/usr/bin/mpv"
ipc_socket = "/run/mloop/mpv.sock"

[display]
connector = "auto"
rotation = 0
mode = "auto"

[audio]
output = "auto"

[hdmi_gestures]
enabled = true
enter_min_disconnect_ms = 800
enter_max_disconnect_ms = 8000
cycle_min_disconnect_ms = 300
cycle_max_disconnect_ms = 5000
debounce_ms = 100
select_after_connected_ms = 5000
menu_timeout_ms = 30000

[menu]
osd_duration_ms = 5000
confirm_dangerous_actions = true

[web]
enabled = false
host = "127.0.0.1"
port = 8080
```

## Playback Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `media_dirs` | list | `["/home/mloop/media"]` | Directories to scan for media files |
| `shuffle` | bool | `false` | Shuffle playlist order |
| `loop` | bool | `true` | Ask the player backend to loop the playlist indefinitely |
| `volume` | int | `80` | Default volume (0-100) |
| `image_duration_seconds` | int | `10` | Duration to display images with the mpv backend |

## Player Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `backend` | string | `"mpv"` | Playback backend |
| `mpv_path` | string | `"/usr/bin/mpv"` | Path to mpv binary |
| `cvlc_path` | string | `"/usr/bin/cvlc"` | Path to cvlc binary |
| `ipc_socket` | string | `"/run/mloop/mpv.sock"` | Path to IPC socket |

## Display Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `connector` | string | `"auto"` | DRM connector name or "auto" |
| `rotation` | int | `0` | Video rotation (0, 90, 180, 270) |
| `mode` | string | `"auto"` | Runtime mode setting is not implemented; use `"auto"` |

## Audio Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output` | string | `"auto"` | Audio output: `"auto"`, `"hdmi"`, or `"system-default"` |

## HDMI Gesture Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable HDMI gesture control |
| `enter_min_disconnect_ms` | int | `800` | Min disconnect time to enter menu |
| `enter_max_disconnect_ms` | int | `8000` | Max disconnect time to enter menu |
| `cycle_min_disconnect_ms` | int | `300` | Min disconnect time for menu navigation |
| `cycle_max_disconnect_ms` | int | `5000` | Max disconnect time for menu navigation |
| `debounce_ms` | int | `100` | Debounce time for HDMI events; must be below `cycle_min_disconnect_ms` |
| `select_after_connected_ms` | int | `5000` | Time connected to select menu item |
| `menu_timeout_ms` | int | `30000` | Menu timeout |

## Menu Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `osd_duration_ms` | int | `5000` | OSD display duration |
| `confirm_dangerous_actions` | bool | `true` | Require confirmation for dangerous actions |

## Web Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Must remain `false`; web interface is not implemented |
| `host` | string | `"127.0.0.1"` | Web interface host |
| `port` | int | `8080` | Web interface port |

## Validation Rules

MLOOP validates configuration during startup. Invalid values stop the daemon with a clear error.

- `player.backend` must be `mpv` or `cvlc`.
- `playback.volume` must be from 0 to 100.
- `display.rotation` must be 0, 90, 180, or 270.
- `display.mode` must be `auto`; set fixed modes through kernel DRM/KMS options.
- `audio.output` must be `auto`, `hdmi`, or `system-default`.
- `hdmi_gestures.debounce_ms` must be lower than `cycle_min_disconnect_ms`.
- Min gesture timings must be lower than or equal to their matching max timings.
- `web.enabled` must remain `false` until the web interface is implemented.

## Runtime State

Menu changes to `volume`, `rotation`, and `audio_output` are saved to `/var/lib/mloop/state.toml`.
Those values override the matching defaults from `/etc/mloop/config.toml` on the next daemon start.
