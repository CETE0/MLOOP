# MLOOP Baseline Project Plan

MLOOP is an open-source Raspberry Pi video looper for galleries, museums, exhibitions, and kiosk installations. Its baseline goal is to behave like a reliable fullscreen media looper by default, while validating a no-keyboard configuration path controlled through HDMI unplug/replug gestures.

This document describes the recommended baseline architecture, repository structure, implementation phases, and open-source project practices.

---

## 1. Product baseline

### 1.1 Core idea

MLOOP should boot directly into fullscreen media playback. If the user does nothing, it should behave like a normal museum/gallery video looper.

If the user unplugs and replugs the HDMI cable within a configured time window, MLOOP should enter a simple on-screen configuration mode. In that menu, the same HDMI unplug/replug action acts like a single-button interface.

This HDMI gesture workflow is a product hypothesis for the baseline, not yet an industry-proven control pattern. Raspberry Pi and Linux DRM/KMS support hotplug detection, but MLOOP must prove on real hardware that the gesture timing is reliable, understandable, and does not compromise playback recovery.

Example flow:

1. Raspberry Pi boots.
2. MLOOP starts automatically.
3. Videos loop fullscreen.
4. Staff unplugs HDMI for 1–8 seconds and reconnects it.
5. MLOOP enters configuration mode.
6. Repeated unplug/replug cycles navigate options.
7. Waiting while connected selects the highlighted option.
8. Timeout returns to playback.

### 1.2 Target users

- Gallery/museum staff
- Artists installing video work
- Exhibition technicians
- Small cultural spaces without IT support
- Digital signage users who need an offline appliance

### 1.3 Design principles

- **Playback first:** never let configuration features compromise reliable looping.
- **No keyboard required:** HDMI gesture menu should cover common actions once hardware validation proves it reliable enough.
- **No network required:** the device should work offline.
- **Recover automatically:** crashes, missing media, HDMI disconnects, and player failures should be handled gracefully.
- **Transparent configuration:** use plain text config files.
- **Modern Raspberry Pi stack:** target Raspberry Pi OS Lite Bookworm or newer, KMS/DRM, systemd, and an IPC-controllable player backend.
- **Open-source friendly:** clean repo structure, documentation, issues, contributing guide, license, tests, and packaging.

---

## 2. Initial technical direction

### 2.1 Operating system target

Recommended baseline:

```txt
Raspberry Pi OS Lite Bookworm or newer
KMS/DRM graphics stack
systemd service startup
mpv as preferred playback backend, pending hardware validation
Python 3 for daemon MVP
```

Avoid for the baseline:

- `omxplayer`
- legacy-only Raspberry Pi graphics behavior
- `.bashrc` autostart
- desktop-only assumptions
- requiring X11/Wayland for the core daemon

### 2.2 Playback backend

Use `mpv` controlled over JSON IPC as the preferred baseline backend.

Reasons:

- strong command-line playback support
- scriptable over local Unix socket
- supports playlists, loop modes, filters, volume, OSD messages
- easier to supervise than a full desktop media player

Validation caveat:

Raspberry Pi documentation currently emphasizes VLC/cvlc for playback on Raspberry Pi OS Lite. mpv remains attractive because its JSON IPC is well suited to a daemon-controlled appliance, but the baseline must validate fullscreen playback, hardware decode behavior, HDMI reconnect behavior, and audio recovery on target Pi models before treating mpv as final.

Example launch shape:

```bash
mpv \
  --fullscreen \
  --idle=yes \
  --loop-playlist=inf \
  --input-ipc-server=/run/mloop/mpv.sock \
  --osd-level=1
```

Important security note: mpv IPC is not a secure network protocol. Use a local Unix socket only.

### 2.3 HDMI detection

Detect HDMI state through Linux DRM/KMS connector status files and/or udev events.

Common connector paths:

```txt
/sys/class/drm/card?-HDMI-A-1/status
/sys/class/drm/card?-HDMI-A-2/status
/sys/class/drm/card?-HDMI-A-1/edid
/sys/class/drm/card?-HDMI-A-1/modes
```

Possible statuses:

```txt
connected
disconnected
unknown
```

Baseline implementation should support:

1. polling `/sys/class/drm/.../status`
2. optional udev event watcher
3. debouncing
4. connector auto-detection
5. explicit connector override in config

Hardware discovery should also capture `kmsprint | grep Connector` when available, because Raspberry Pi documentation recommends it for listing DRM output names.

### 2.4 HDMI forcing caveat

For reliability, kiosk systems often force HDMI modes. On modern KMS systems this may involve kernel command line options such as:

```txt
video=HDMI-A-1:1280x720@60D
```

or file-based EDID:

```txt
drm.edid_firmware=HDMI-A-1:myedid.dat
```

However, forced HDMI output may interfere with physical hotplug detection. MLOOP should treat this as a documented compatibility mode:

- Auto HDMI mode: HDMI gestures are expected to be testable and are more likely to work.
- Forced output mode: playback may be more reliable, but HDMI gestures may be unavailable or less reliable.

The app should expose this clearly in docs and config.

---

## 3. Baseline feature set

### 3.1 MVP features

The baseline version should include:

- automatic fullscreen playback on boot
- media folder scanning
- playlist generation
- mpv process supervision
- HDMI hotplug detection
- HDMI gesture state machine
- simple on-screen menu using mpv OSD
- persistent config/state
- systemd service
- install script or Debian packaging foundation
- useful logs
- no-media error screen

### 3.2 First menu items

Keep the first menu small and safe:

```txt
1. Resume playback
2. Volume
3. Audio output
4. Rotate video
5. Rescan media
6. Show network info
7. Reboot
8. Shutdown
```

Dangerous actions must require confirmation.

### 3.3 Gesture defaults

Recommended defaults:

```toml
[hdmi_gestures]
enabled = true
enter_min_disconnect_ms = 800
enter_max_disconnect_ms = 8000
cycle_min_disconnect_ms = 300
cycle_max_disconnect_ms = 5000
debounce_ms = 500
select_after_connected_ms = 5000
menu_timeout_ms = 30000
```

Interaction model:

- unplug/replug for 1–8 seconds: enter menu
- quick unplug/replug while in menu: next item
- remain connected for 5 seconds: select item
- no activity for 30 seconds: exit menu

---

## 4. Recommended repository layout

Use a conventional open-source layout from the beginning.

```txt
mloop/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── ROADMAP.md
├── BASELINE_PLAN.md
├── pyproject.toml
├── ruff.toml
├── .gitignore
├── .editorconfig
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── hardware_report.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── docs/
│   ├── index.md
│   ├── installation.md
│   ├── configuration.md
│   ├── hdmi-gestures.md
│   ├── media.md
│   ├── audio.md
│   ├── display.md
│   ├── troubleshooting.md
│   ├── hardware-compatibility.md
│   └── development.md
├── packaging/
│   ├── systemd/
│   │   └── mloop.service
│   ├── debian/
│   │   └── README.md
│   └── install.sh
├── config/
│   ├── mloop.example.toml
│   └── mpv.conf
├── scripts/
│   ├── dev-run.sh
│   ├── collect-debug-info.sh
│   └── simulate-hdmi-events.py
├── src/
│   └── mloop/
│       ├── __init__.py
│       ├── __main__.py
│       ├── daemon.py
│       ├── config.py
│       ├── logging.py
│       ├── media.py
│       ├── player/
│       │   ├── __init__.py
│       │   ├── mpv.py
│       │   └── ipc.py
│       ├── display/
│       │   ├── __init__.py
│       │   ├── drm.py
│       │   ├── hdmi_watcher.py
│       │   └── rotation.py
│       ├── gestures/
│       │   ├── __init__.py
│       │   ├── state_machine.py
│       │   └── events.py
│       ├── menu/
│       │   ├── __init__.py
│       │   ├── model.py
│       │   ├── controller.py
│       │   └── actions.py
│       ├── audio/
│       │   ├── __init__.py
│       │   └── devices.py
│       └── system/
│           ├── __init__.py
│           ├── service.py
│           └── platform.py
└── tests/
    ├── unit/
    │   ├── test_config.py
    │   ├── test_media.py
    │   ├── test_gesture_state_machine.py
    │   └── test_menu.py
    ├── integration/
    │   ├── test_mpv_ipc.py
    │   └── test_hdmi_watcher_fake_sysfs.py
    └── fixtures/
        ├── sysfs_connected/
        ├── sysfs_disconnected/
        └── media_tree/
```

### 4.1 Why this layout

- `src/mloop`: prevents accidental imports from the project root.
- `docs`: makes the project usable by non-developers.
- `packaging`: keeps OS integration separate from application logic.
- `config`: gives users copyable examples.
- `scripts`: useful development and field-debug utilities.
- `tests`: enables confidence in gesture timing and config behavior.
- `.github`: supports healthy open-source collaboration.

---

## 5. Main modules

### 5.1 `mloop.daemon`

Responsibilities:

- load config
- initialize logging
- discover platform capabilities
- start mpv supervisor
- start HDMI watcher
- start media scanner
- route events into gesture/menu controllers
- handle shutdown signals

### 5.2 `mloop.player.mpv`

Responsibilities:

- launch mpv
- maintain IPC socket
- send commands
- restart mpv if it exits unexpectedly
- update playlist
- show OSD messages
- set volume
- apply video rotation filter

### 5.3 `mloop.display.drm`

Responsibilities:

- discover DRM connectors
- read connector status
- read EDID presence
- read available modes
- normalize connector names

Example connector model:

```python
@dataclass
class DrmConnector:
    name: str          # HDMI-A-1
    sysfs_path: Path   # /sys/class/drm/card1-HDMI-A-1
    status: str        # connected/disconnected/unknown
```

### 5.4 `mloop.display.hdmi_watcher`

Responsibilities:

- watch HDMI state changes
- debounce events
- emit normalized events
- support fake sysfs path for tests

Normalized events:

```python
@dataclass
class HdmiEvent:
    connector: str
    state: Literal["connected", "disconnected", "unknown"]
    monotonic_ms: int
```

### 5.5 `mloop.gestures.state_machine`

Responsibilities:

- convert HDMI events into user intents
- track disconnect duration
- distinguish accidental cable loss from menu entry gesture
- emit menu navigation/select/cancel events

Possible emitted intents:

```python
class GestureIntent(Enum):
    ENTER_MENU = "enter_menu"
    NEXT_ITEM = "next_item"
    SELECT_ITEM = "select_item"
    TIMEOUT = "timeout"
```

This module should be heavily unit tested.

### 5.6 `mloop.menu`

Responsibilities:

- represent menu items
- handle cursor movement
- trigger actions
- render menu state through mpv OSD
- confirm dangerous actions

Baseline rendering can use mpv `show-text` rather than a full graphical UI.

### 5.7 `mloop.media`

Responsibilities:

- scan configured media directories
- filter supported extensions
- sort predictably
- build playlist
- detect no-media state
- optionally watch directories for changes later

Recommended default supported extensions:

```txt
.mp4
.mov
.mkv
.webm
.m4v
.mp3
.wav
.flac
.jpg
.png
.jpeg
```

### 5.8 `mloop.audio.devices`

Responsibilities:

- list possible audio outputs
- map friendly names to mpv/ALSA/PipeWire device IDs
- apply selected audio output

For the MVP, keep this conservative. Use `auto`, `hdmi`, and `system-default` first. Add analog/USB detection once tested on real hardware.

---

## 6. Configuration design

### 6.1 Config locations

Use system-level defaults and persistent state separately:

```txt
/etc/mloop/config.toml       # user-editable config
/var/lib/mloop/state.toml    # runtime/user menu changes
/run/mloop/mpv.sock          # mpv IPC socket
/var/log/mloop/mloop.log     # optional log file, or use journald
```

### 6.2 Example config

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

---

## 7. System service baseline

Use systemd. Do not start from `.bashrc`.

Example service:

```ini
[Unit]
Description=MLOOP video looper
After=multi-user.target sound.target
Wants=sound.target

[Service]
Type=simple
User=mloop
Group=mloop
RuntimeDirectory=mloop
StateDirectory=mloop
LogsDirectory=mloop
ExecStart=/usr/bin/mloopd
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

Implementation notes:

- create a dedicated `mloop` user
- keep writable state under `/var/lib/mloop`
- keep runtime sockets under `/run/mloop`
- use journald by default
- add `WatchdogSec=` only after `mloopd` implements systemd watchdog notifications
- provide `collect-debug-info.sh` for issue reports

---

## 8. Development phases

### Phase 0: Repository foundation

Create:

- README
- license
- contributing guide
- code of conduct
- security policy
- changelog
- roadmap
- docs skeleton
- Python package skeleton
- CI for lint/type/test

Deliverable:

```txt
Project can be cloned, installed in editable mode, linted, and tested.
```

### Phase 1: mpv playback prototype

Implement:

- config loader
- media scanner
- mpv launcher
- mpv IPC client
- fullscreen playlist loop
- no-media OSD/error state
- hardware notes comparing mpv behavior against cvlc on at least one Raspberry Pi

Deliverable:

```txt
mloopd plays media from a configured folder using mpv, restarts mpv if it crashes, and records whether mpv is acceptable as the baseline player on tested hardware.
```

### Phase 2: HDMI watcher prototype

Implement:

- DRM connector discovery
- connector status polling
- debounced HDMI events
- fake sysfs fixtures for tests
- logging of raw HDMI events
- hardware probe output collection: `kmsprint | grep Connector`, `/sys/class/drm/*/status`, EDID presence, and available modes

Deliverable:

```txt
mloopd logs connected/disconnected events reliably on target Raspberry Pi hardware and documents any connector naming or status anomalies.
```

### Phase 3: Gesture state machine

Implement:

- event-to-intent conversion
- menu entry gesture
- menu navigation gesture
- selection timeout
- exit timeout
- unit tests for edge cases

Deliverable:

```txt
HDMI unplug/replug sequences are converted into deterministic menu intents in tests and the expected timing remains adjustable for hardware validation.
```

### Phase 4: Menu MVP

Implement:

- OSD menu rendering via mpv
- resume playback
- volume change
- rotate video
- rescan media
- show network info
- reboot confirmation
- shutdown confirmation

Deliverable:

```txt
A user can configure basic settings using only HDMI unplug/replug gestures on hardware where the gesture workflow has been validated.
```

### Phase 5: System integration

Implement:

- systemd service
- install script
- default config installation
- dedicated user creation
- log collection script
- first real hardware install guide

Deliverable:

```txt
Fresh Raspberry Pi OS Lite install can become an MLOOP appliance using documented commands.
```

### Phase 6: Compatibility testing

Test matrix:

```txt
Pi 3, Pi 4, Pi 5 if available
HDMI-A-1 and HDMI-A-2 on Pi 4/5
1080p display
720p display
HDMI audio display
DVI/HDMI adapter
cheap HDMI cable
HDMI splitter/extender if available
forced output mode
normal auto output mode
mpv playback
cvlc playback comparison
```

Deliverable:

```txt
Documented hardware compatibility table and known limitations.
```

Minimum compatibility evidence per tested setup:

- Pi model and OS image date/version
- display model and physical HDMI port
- `kmsprint | grep Connector` output when available
- `/sys/class/drm/*/status` before, during, and after disconnect
- player backend tested: mpv and/or cvlc
- whether video resumes after reconnect
- whether HDMI audio resumes after reconnect
- whether forced output mode changes hotplug status behavior
- observed reconnect-to-visible-image delay
- whether staff can perform the gesture without precise timing

---

## 9. Testing strategy

### 9.1 Unit tests

High-priority unit tests:

- config loading and defaults
- media file filtering
- playlist ordering
- gesture timing thresholds
- menu navigation
- dangerous action confirmation
- fake DRM connector parsing

### 9.2 Integration tests

Use fake sysfs directories to simulate HDMI status changes.

Example fixture:

```txt
tests/fixtures/sysfs_connected/card1-HDMI-A-1/status
tests/fixtures/sysfs_disconnected/card1-HDMI-A-1/status
```

Test that the watcher can run against a configurable root instead of hardcoded `/sys/class/drm`.

### 9.3 Hardware tests

Manual hardware tests should be documented as checklists:

- boot with HDMI connected
- boot with HDMI disconnected
- disconnect during playback
- reconnect during playback
- enter menu through gesture
- navigate all menu items
- change volume
- change rotation
- rescan media
- reboot from menu
- shutdown from menu
- recover from mpv crash
- compare mpv and cvlc playback on at least one representative file
- record CPU load, visible stutter, loop gap, audio behavior, and reconnect behavior

---

## 10. Documentation plan

### 10.1 README

The README should include:

- what MLOOP is
- who it is for
- hardware requirements
- quick install
- quick usage
- HDMI gesture explanation
- limitations
- project status
- links to docs

### 10.2 Installation docs

Include:

- Raspberry Pi OS Lite setup
- dependency installation
- MLOOP installation
- enabling systemd service
- adding media
- troubleshooting no display/no audio

### 10.3 HDMI gesture docs

Explain:

- how to enter menu
- timing
- how to navigate
- how to select
- how to cancel
- compatibility caveats
- forced HDMI caveat

### 10.4 Troubleshooting docs

Include sections for:

- no video output
- no audio
- HDMI menu does not trigger
- display goes black after boot
- mpv fails to start
- media not detected
- collecting logs

---

## 11. Open-source project practices

### 11.1 License

Recommended license: **GPL-3.0-or-later** if you want to ensure improvements remain open, or **MIT/Apache-2.0** if you want maximum permissive adoption.

For museum/gallery infrastructure, GPL-3.0-or-later is reasonable if the project values software freedom. MIT is reasonable if broad hardware vendor adoption is more important.

Pick one early and add `LICENSE`.

### 11.2 Issue templates

Use three templates:

- bug report
- feature request
- hardware compatibility report

Hardware reports should ask for:

- Raspberry Pi model
- OS version
- display model
- HDMI port used
- cable/adapter/splitter
- audio output
- whether forced HDMI mode is enabled
- logs from `collect-debug-info.sh`

### 11.3 Contributing guide

Explain:

- development setup
- branch naming
- test commands
- style rules
- how to add hardware compatibility data
- how to write docs
- pull request expectations

### 11.4 Security policy

Mention:

- mpv IPC is local-only
- web UI, when added, is disabled by default
- report vulnerabilities privately through GitHub security advisories or listed email

### 11.5 CI

Baseline CI should run:

```bash
ruff check .
ruff format --check .
pytest
```

Optionally add:

```bash
mypy src
```

---

## 12. Implementation recommendations

### 12.1 Language choice

Use Python for the baseline.

Reasons:

- fast prototyping
- good Raspberry Pi support
- easy system integration
- simple file and process management
- easy testing of state machines

Rust could be considered later for a hardened daemon, but Python is better for the initial open-source baseline.

### 12.2 Dependency policy

Keep dependencies minimal.

Recommended baseline dependencies:

- `tomli` only if supporting Python versions before 3.11
- maybe `pyudev` for udev event support
- test dependencies: `pytest`, `ruff`

Avoid requiring a heavy GUI toolkit for MVP.

### 12.3 Logging

Use structured, readable logs. Include:

- config path loaded
- selected DRM connector
- HDMI raw events
- gesture interpretations
- mpv start/stop/restart
- playlist changes
- menu actions
- errors with remediation hints

Example log line:

```txt
HDMI event connector=HDMI-A-1 state=disconnected duration_ms=0 source=poll
Gesture intent=ENTER_MENU disconnect_duration_ms=2140
```

---

## 13. Field-debug script

Create `scripts/collect-debug-info.sh` to collect:

```bash
uname -a
cat /etc/os-release
systemctl status mloop --no-pager
journalctl -u mloop -n 300 --no-pager
ls -la /sys/class/drm
cat /sys/class/drm/card*-HDMI-A-*/status
cat /sys/class/drm/card*-HDMI-A-*/modes
kmsprint | grep Connector || true
aplay -l
aplay -L | grep sysdefault || true
wpctl status || true
pactl info || true
mpv --version
cvlc --version || true
```

This is crucial for open-source support.

---

## 14. Key risks to validate early

Prototype these before spending time on polish:

1. Can the target Pi detect HDMI unplug/replug reliably under Bookworm Lite?
2. Does mpv perform well enough on Pi 3/4/5 compared with cvlc for fullscreen looping?
3. Does mpv survive HDMI disconnect/reconnect during playback?
4. Does HDMI audio recover after reconnect?
5. Does forced HDMI mode hide physical hotplug events?
6. Are Pi 4/5 connector names stable enough for auto-detection?
7. How long do common displays take to show image after reconnect?
8. Can staff perform gestures comfortably without precise timing?

---

## 15. Baseline success criteria

The baseline is successful when:

- Raspberry Pi boots into fullscreen looping playback.
- Removing/reconnecting HDMI does not crash the app.
- A documented HDMI gesture opens the menu on validated hardware/configurations.
- A user can change at least volume, rotation, and rescan media using only HDMI gestures on validated hardware/configurations.
- mpv is supervised and restarted after failure.
- mpv has been validated against cvlc for the supported baseline hardware, or the plan explicitly switches backend.
- Config persists across reboot.
- The app runs as a systemd service.
- The repo has README, license, contributing guide, tests, and CI.
- A new contributor can understand the architecture from docs.

---

## 16. Suggested first milestone checklist

```txt
[x] Create repository skeleton
[x] Choose license
[x] Add README
[x] Add pyproject.toml
[x] Add src/mloop package
[x] Add config loader
[x] Add media scanner
[x] Add mpv launcher
[x] Add mpv IPC show-text command
[x] Add fake HDMI event simulator
[x] Add gesture state machine tests
[x] Add systemd service draft
[x] Add install docs draft
[ ] Test on real Raspberry Pi with one display
[ ] Document first hardware results
```

---

## 17. Recommended project status wording

Until real hardware testing is complete, the README should clearly say:

```txt
Project status: experimental prototype.

MLOOP is being developed for Raspberry Pi OS Lite Bookworm and modern KMS/DRM systems. HDMI gesture control depends on display, cable, Raspberry Pi model, and video mode configuration. Please see the hardware compatibility table before using in production installations.
```

This sets correct expectations and invites useful community testing.

---

## 18. Research basis for baseline decisions

These findings should guide implementation until MLOOP has its own compatibility data:

- `mpv` JSON IPC is documented for local external control over Unix sockets and supports commands/properties suitable for OSD, volume, playlist, and process supervision. Its IPC interface is explicitly not secure, so MLOOP must keep it on a local socket under `/run/mloop`.
- Raspberry Pi OS Lite documentation emphasizes VLC/cvlc for command-line media playback. MLOOP can still prefer mpv because IPC control is central to the daemon design, but mpv must be validated against cvlc on target hardware.
- `omxplayer` should not be used for the baseline. It is deprecated and tied to legacy Raspberry Pi graphics/media APIs rather than modern KMS/DRM systems.
- Linux DRM/KMS exposes hotpluggable display connectors and connector status through userspace-visible interfaces. Raspberry Pi documentation uses DRM connector names such as `HDMI-A-1` and `HDMI-A-2`, matching the planned auto-detection model.
- Similar Raspberry Pi looper projects validate the general appliance pattern: boot into playback, scan media, loop playlists, use plain configuration, and provide installation docs. They do not validate HDMI unplug/replug as a common menu-control pattern, so MLOOP must treat that workflow as experimental.
- systemd `RuntimeDirectory=`, `StateDirectory=`, and `LogsDirectory=` match the planned `/run/mloop`, `/var/lib/mloop`, and `/var/log/mloop` layout. `WatchdogSec=` should only be enabled after the daemon sends watchdog notifications.
- Python `src/` layout, `pyproject.toml`, pytest, ruff, CI, issue templates, `SECURITY.md`, `CONTRIBUTING.md`, and a license match current Python packaging and open-source project practice.
