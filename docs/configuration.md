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
debounce_ms = 500
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
| `loop` | bool | `true` | Loop playlist indefinitely |
| `volume` | int | `80` | Default volume (0-100) |
| `image_duration_seconds` | int | `10` | Duration to display images |

## Player Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `backend` | string | `"mpv"` | Playback backend |
| `mpv_path` | string | `"/usr/bin/mpv"` | Path to mpv binary |
| `ipc_socket` | string | `"/run/mloop/mpv.sock"` | Path to IPC socket |

## Display Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `connector` | string | `"auto"` | DRM connector name or "auto" |
| `rotation` | int | `0` | Video rotation (0, 90, 180, 270) |
| `mode` | string | `"auto"` | Display mode or "auto" |

## Audio Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output` | string | `"auto"` | Audio output device |

## HDMI Gesture Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable HDMI gesture control |
| `enter_min_disconnect_ms` | int | `800` | Min disconnect time to enter menu |
| `enter_max_disconnect_ms` | int | `8000` | Max disconnect time to enter menu |
| `cycle_min_disconnect_ms` | int | `300` | Min disconnect time for menu navigation |
| `cycle_max_disconnect_ms` | int | `5000` | Max disconnect time for menu navigation |
| `debounce_ms` | int | `500` | Debounce time for HDMI events |
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
| `enabled` | bool | `false` | Enable web interface |
| `host` | string | `"127.0.0.1"` | Web interface host |
| `port` | int | `8080` | Web interface port |
