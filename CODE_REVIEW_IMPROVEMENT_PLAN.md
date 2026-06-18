# MLOOP Improvement Plan

**Date:** 2026-06-16  
**Source review:** `CODE_REVIEW.md`  
**Scope:** Plan only — no implementation in this document  
**Commit baseline:** `f6418f2`

---

## Goals

1. Make the packaged daemon (`mloopd` + systemd service) actually start and remain healthy.
2. Align runtime behavior with documented configuration.
3. Make player crash recovery reliable for both mpv and cvlc.
4. Make HDMI gesture timing deterministic enough for field use.
5. Remove blocking work from the asyncio loop and supervise background tasks.
6. Decide whether persistence/web/display-mode/cvlc controls are supported features or roadmap items.
7. Restore and enforce quality gates.

## Non-goals for this plan

- Do **not** implement changes yet.
- Do **not** redesign the whole architecture.
- Do **not** add new runtime dependencies unless called out explicitly as a deliberate choice.

---

## Recommended implementation order

| Phase | Priority | Theme | Main issues covered |
|-------|----------|-------|---------------------|
| 1 | Critical | Entrypoint + CI smoke | C1, H8 |
| 2 | High | Player lifecycle/recovery | H1, H7, H3 partial |
| 3 | High | Menu/gesture correctness | H2, H4, M5 |
| 4 | High | Async hygiene | H5, H6 |
| 5 | Medium | Config/state correctness | H3, M1, M2, M4, M6, M7 |
| 6 | Medium | Backend capabilities | M3 |
| 7 | Low | Installer/docs/type polish | M8, L1-L7 |

---

# Phase 1 — Fix production entrypoint and quality gate basics [COMPLETED]

## 1.1 Make `mloopd` synchronous [COMPLETED]

### Problem

`pyproject.toml` points the console script to `mloop.__main__:main`, but `main()` is currently
`async def`. A setuptools console-script wrapper calls the target synchronously, so it gets a
coroutine object and never runs the daemon.

### Target design

- Rename current async body to `_amain()`.
- Make `main()` a synchronous wrapper that calls `asyncio.run(_amain())`.
- Preserve `python -m mloop` behavior by calling `main()` in the module guard.
- Remove unused `Config` import while touching this file.

### Planned snippet

```python
# src/mloop/__main__.py
"""MLOOP daemon entry point."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from mloop.config import load_config
from mloop.daemon import Daemon


async def _amain() -> None:
    """Run the MLOOP daemon asynchronously."""
    config_dir = os.environ.get("MLOOP_CONFIG_DIR")
    config_path = Path(config_dir, "config.toml") if config_dir else None
    config = load_config(config_path)
    daemon = Daemon(config=config)

    try:
        await daemon.run()
    except KeyboardInterrupt:
        await daemon.stop()
    except Exception:
        await daemon.stop()
        raise


def main() -> None:
    """Console-script entry point."""
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
```

### Regression tests

```python
# tests/unit/test_entrypoint.py
import inspect

from mloop import __main__


def test_console_entrypoint_is_synchronous() -> None:
    assert not inspect.iscoroutinefunction(__main__.main)
    assert inspect.iscoroutinefunction(__main__._amain)
```

If a fast CLI/dry-run option is added later:

```python
# tests/integration/test_entrypoint_script.py
import subprocess
import sys


def test_mloopd_help_exits_successfully() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "mloop", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
```

> Note: today there is no CLI parser/help path, so the first test is the immediate fix.

---

## 1.2 Restore ruff and decide mypy policy [COMPLETED]

### Problem

Local checks currently show:

```text
ruff: F401 unused Config import in src/mloop/__main__.py
mypy: config.py: "type" has no attribute "__dataclass_fields__"
```

CI runs ruff + pytest but does not run mypy, despite `mypy>=1.0` being a dev dependency.

### Target design

- Fix ruff immediately via entrypoint cleanup.
- Add a mypy config and CI job **or** remove mypy from dev dependencies.
- Preferred: keep mypy and start with modest strictness.

### Planned config snippet

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
packages = ["mloop"]
warn_unused_configs = true
warn_return_any = true
warn_unused_ignores = true
no_implicit_optional = true
check_untyped_defs = true
```

### Planned CI snippet

```yaml
# .github/workflows/ci.yml
- name: Type check with mypy
  run: |
    mypy src/mloop
```

### Fix for `_parse_section` typing

```python
from dataclasses import fields, is_dataclass
from typing import TypeVar

T = TypeVar("T")


def _parse_section(data: dict[str, Any], cls: type[T]) -> T:
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")

    defaults_dict: dict[str, Any] = {}
    for field_info in fields(cls):
        ...

    return cls(**merged)
```

---

# Phase 2 — Player lifecycle and crash recovery

## 2.1 Introduce explicit player lifecycle reset/restart semantics

### Problem

`Daemon._run_main_loop()` only calls `self.player.start()` after a crash. That:

- starts mpv idle with no playlist,
- starts cvlc with no media files,
- leaves mpv IPC state stale,
- does not reapply volume/rotation/audio settings,
- has no retry backoff.

### Target design

Add a backend method for clearing runtime connections/state and make daemon recovery:

1. detect unexpected exit,
2. stop/reset backend state,
3. sleep according to backoff,
4. start backend,
5. reload playlist,
6. reapply current runtime settings,
7. increase backoff on failure and reset it after success.

### Backend interface snippet

```python
# src/mloop/player/backend.py
class PlayerBackend(ABC):
    ...

    async def reset_after_exit(self) -> None:
        """Clear transient state after the player process exits unexpectedly."""
        return None
```

For mpv:

```python
# src/mloop/player/mpv.py
async def reset_after_exit(self) -> None:
    if self._ipc is not None:
        await self._ipc.disconnect()
        self._ipc = None
    self._process = None
    self._running = False
```

For cvlc:

```python
# src/mloop/player/cvlc.py
async def reset_after_exit(self) -> None:
    self._process = None
    self._running = False
```

### Daemon recovery snippet

```python
# src/mloop/daemon.py
async def _recover_player(self) -> None:
    self.logger.warning("%s exited unexpectedly, restarting", type(self.player).__name__)

    await self.player.reset_after_exit()

    delay = self._player_restart_backoff_seconds
    if delay > 0:
        await asyncio.sleep(delay)

    try:
        self.player.start()
        await self._load_media()
        await self._apply_player_state()
    except Exception:
        self._player_restart_backoff_seconds = min(
            max(1.0, self._player_restart_backoff_seconds * 2),
            60.0,
        )
        self.logger.exception(
            "Player restart failed; next retry in %.1fs",
            self._player_restart_backoff_seconds,
        )
        return

    self._player_restart_backoff_seconds = 0.0
```

Call from loop:

```python
if not self.player.is_running:
    await self._recover_player()
```

### Regression test snippet

```python
@pytest.mark.asyncio
async def test_player_crash_reloads_media(monkeypatch, tmp_path):
    config = Config()
    daemon = Daemon(config)

    calls: list[str] = []

    class FakePlayer:
        is_running = False
        def start(self): calls.append("start"); self.is_running = True
        def stop(self): calls.append("stop")
        async def reset_after_exit(self): calls.append("reset")
        async def load_playlist(self, files): calls.append("load_playlist")
        async def set_volume(self, volume): calls.append(f"volume:{volume}")
        async def set_rotation(self, degrees): calls.append(f"rotation:{degrees}")
        async def set_audio_output(self, output): calls.append(f"audio:{output}")
        async def show_osd(self, text, duration=5000): pass
        @property
        def pid(self): return 123

    daemon.player = FakePlayer()
    monkeypatch.setattr("mloop.daemon.scan_media_dirs", lambda _: [tmp_path / "a.mp4"])

    await daemon._recover_player()

    assert calls[:3] == ["reset", "start", "load_playlist"]
    assert "volume:80" in calls
```

---

## 2.2 Catch the correct player stop timeout

### Problem

`subprocess.Popen.wait(timeout=...)` raises `subprocess.TimeoutExpired`, not built-in
`TimeoutError`.

### Planned snippet

```python
# src/mloop/player/mpv.py and cvlc.py
try:
    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
    self._process.wait(timeout=5)
except subprocess.TimeoutExpired:
    logger.warning("Player did not exit after SIGTERM; sending SIGKILL")
    with contextlib.suppress(ProcessLookupError):
        os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
        self._process.wait(timeout=5)
except ProcessLookupError:
    pass
finally:
    self._process = None
    self._running = False
```

### Regression test idea

Use a fake process whose `wait(timeout=...)` raises `subprocess.TimeoutExpired` on the first
call and succeeds after SIGKILL. Assert `os.killpg` receives both `SIGTERM` and `SIGKILL`.

---

## 2.3 Apply documented playback settings on startup and recovery

### Problem

`volume`, `rotation`, `audio.output`, `image_duration_seconds`, and `loop` are documented but
not consistently applied.

### Target design

- Keep runtime state in a dataclass.
- Apply state after `player.start()` and after crash recovery.
- Pass static player startup options before process launch where required.

### Player state snippet

```python
# src/mloop/daemon.py
from dataclasses import dataclass

@dataclass
class PlayerState:
    volume: int
    rotation: int
    audio_output: str

# Daemon.__init__
self.state = PlayerState(
    volume=self.config.playback.volume,
    rotation=self.config.display.rotation,
    audio_output=self.config.audio.output,
)
```

### Apply state snippet

```python
async def _apply_player_state(self) -> None:
    await self.player.set_volume(self.state.volume)
    await self.player.set_rotation(self.state.rotation)
    await self.player.set_audio_output(self.state.audio_output)
```

### mpv startup option snippet

Preferred: extend `PlayerConfig` or pass full `Config`/`PlaybackConfig` to `MpvPlayer`.

```python
args = [
    self.config.mpv_path,
    "--fullscreen",
    "--idle=yes",
    f"--loop-playlist={'inf' if self.playback_config.loop else 'no'}",
    f"--image-display-duration={self.playback_config.image_duration_seconds}",
    f"--input-ipc-server={socket_path}",
    "--osd-level=1",
    "--no-terminal",
]
```

Alternative: set mpv properties after IPC connect where possible, but
`--image-display-duration` is naturally a process option.

---

# Phase 3 — Menu and HDMI gesture correctness

## 3.1 Register only one menu controller

### Problem

The daemon registers a stale empty menu controller and then a real menu controller. Every gesture
intent is delivered twice.

### Target design

- Build menu once before registering gesture callbacks.
- Do not create a throwaway controller in `__init__`.

### Planned snippet

```python
# Daemon.__init__
self.menu_model: MenuModel | None = None
self.menu_controller: MenuController | None = None

# Daemon.run
self._build_menu()
self._setup_gesture_handlers()
```

```python
def _setup_gesture_handlers(self) -> None:
    if self.menu_controller is None:
        raise RuntimeError("Menu must be built before registering handlers")
    self.gesture_machine.on_intent(self.menu_controller.handle_intent)
```

If callbacks need rebuild support:

```python
# src/mloop/gestures/state_machine.py
def clear_intent_callbacks(self) -> None:
    self._callbacks.clear()
```

### Regression test snippet

```python
def test_daemon_registers_one_menu_controller() -> None:
    daemon = Daemon(Config())
    daemon._build_menu()
    daemon._setup_gesture_handlers()
    assert len(daemon.gesture_machine._callbacks) == 1
```

---

## 3.2 Fix debounce vs gesture timing

### Problem

Defaults:

```python
cycle_min_disconnect_ms = 300
debounce_ms = 500
poll_interval_ms = 200
```

A valid quick cycle can occur entirely inside the debounce window and be missed, or the reconnect
edge can be delayed enough to distort the measured duration.

### Options

#### Option A — Lower default debounce

Simplest and likely sufficient:

```python
@dataclass
class HdmiGesturesConfig:
    cycle_min_disconnect_ms: int = 300
    debounce_ms: int = 100
```

Add validation:

```python
if config.hdmi_gestures.debounce_ms >= config.hdmi_gestures.cycle_min_disconnect_ms:
    raise ConfigError("hdmi_gestures.debounce_ms must be less than cycle_min_disconnect_ms")
```

#### Option B — Stabilization debounce

Track raw status changes separately from emitted stable state. Emit an edge only after the new
raw state has remained stable for `debounce_ms`.

```python
@dataclass
class _ConnectorDebounceState:
    emitted_state: str
    raw_state: str
    raw_changed_ms: int

async def _poll(self) -> None:
    now = self._now_ms()
    for connector in self.connectors:
        current = connector.read_status()
        state = self._states[connector.name]

        if current != state.raw_state:
            state.raw_state = current
            state.raw_changed_ms = now
            continue

        stable_for = now - state.raw_changed_ms
        if current != state.emitted_state and stable_for >= self.debounce_ms:
            state.emitted_state = current
            self._emit(HdmiEvent(connector.name, current, now))
```

This avoids emitting bounces, but still has limitations with slow polling. Lowering poll interval
may also be needed.

#### Option C — Event source beyond polling

Longer-term: use udev/netlink/DRM events where available instead of only 200 ms polling. Keep
polling as fallback.

### Recommended immediate fix

Use Option A now (`debounce_ms = 100` or `150`) plus validation. Consider Option B later if real
hardware shows noise.

### Regression tests

```python
@pytest.mark.asyncio
async def test_quick_cycle_after_menu_open_emits_both_edges(fake_connector):
    watcher = TestableHdmiWatcher([fake_connector], debounce_ms=100, poll_interval_ms=50)
    events = []
    watcher.on_event(events.append)

    # initialize as connected
    watcher.set_time(0)
    watcher.initialize_for_test()

    fake_connector.write_status("disconnected")
    watcher.set_time(100)
    await watcher._poll()

    fake_connector.write_status("connected")
    watcher.set_time(450)
    await watcher._poll()

    assert [e.state for e in events] == ["disconnected", "connected"]
```

```python
def test_300ms_cycle_in_menu_open_yields_next_item() -> None:
    cfg = HdmiGesturesConfig(cycle_min_disconnect_ms=300)
    machine = GestureStateMachine(cfg)
    intents = []
    machine.on_intent(intents.append)

    machine.handle_event(HdmiEvent("HDMI-A-1", "disconnected", 1000))
    machine.handle_event(HdmiEvent("HDMI-A-1", "connected", 2000))
    assert GestureIntent.ENTER_MENU in intents

    machine.handle_event(HdmiEvent("HDMI-A-1", "disconnected", 3000))
    machine.handle_event(HdmiEvent("HDMI-A-1", "connected", 3300))
    assert GestureIntent.NEXT_ITEM in intents
```

---

## 3.3 Reduce menu-open source-of-truth drift

### Problem

`GestureStateMachine.is_menu_open` and `MenuModel.is_open` can diverge.

### Target design options

#### Option A — Menu model is UI state, gesture machine is input state

Keep both but synchronize explicitly:

```python
# Daemon._on_hdmi_event or after timeout checks
if self.gesture_machine.is_menu_open != self.menu_model.is_open:
    self.logger.warning(
        "Menu state drift: gesture=%s model=%s",
        self.gesture_machine.is_menu_open,
        self.menu_model.is_open,
    )
```

#### Option B — Controller owns menu state

Gesture machine emits intents only; menu controller/model decides open/closed. Daemon only checks
`menu_model.is_open`.

This is closest to current behavior. If using Option B, remove public `is_menu_open` from gesture
machine or use it only in tests.

#### Option C — Gesture machine owns open state

Menu model becomes render/cursor only. This is a larger change and not recommended immediately.

### Recommended

Use Option B and add invariant tests around timeout/select flows.

---

# Phase 4 — Async hygiene

## 4.1 Supervise background tasks

### Problem

`asyncio.create_task()` is used without retaining references. Python docs warn tasks may be
garbage-collected if not strongly referenced, and exceptions are not handled.

### Target design

Add a small task supervisor to `Daemon` and long-lived task references in IPC.

### Daemon task supervisor snippet

```python
# src/mloop/daemon.py
from collections.abc import Coroutine
from typing import Any

class Daemon:
    def __init__(...) -> None:
        ...
        self._background_tasks: set[asyncio.Task[Any]] = set()

    def _spawn_background(self, coro: Coroutine[Any, Any, Any], name: str) -> None:
        task = asyncio.create_task(coro, name=name)
        self._background_tasks.add(task)
        task.add_done_callback(self._on_background_task_done)

    def _on_background_task_done(self, task: asyncio.Task[Any]) -> None:
        self._background_tasks.discard(task)
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            self.logger.exception("Background task failed: %s", task.get_name())
```

Use it in HDMI event handling:

```python
if self.menu_model.is_open:
    self._spawn_background(
        self.player.show_osd(self.menu_model.render(), self.config.menu.osd_duration_ms),
        "show-menu-osd",
    )
```

Stop cleanup:

```python
for task in self._background_tasks:
    task.cancel()
await asyncio.gather(*self._background_tasks, return_exceptions=True)
self._background_tasks.clear()
```

### IPC read-loop supervision snippet

```python
# src/mloop/player/ipc.py
class MpvIpcClient:
    def __init__(...) -> None:
        ...
        self._read_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        ...
        self._read_task = asyncio.create_task(self._read_loop(), name="mpv-ipc-read")

    async def disconnect(self) -> None:
        if self._read_task is not None:
            self._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._read_task
            self._read_task = None
        ...
```

### Menu action options

Current actions are sync closures that spawn async player calls. Prefer converting action
execution to support async callables.

```python
# src/mloop/menu/model.py
Action = Callable[[], Awaitable[None] | None]

@dataclass
class MenuItem:
    label: str
    action: Action
```

```python
# src/mloop/menu/controller.py
async def handle_intent(self, intent: GestureIntent) -> None:
    ...

async def _execute_action(self, item: MenuItem) -> None:
    result = item.action()
    if inspect.isawaitable(result):
        await result
```

This is a larger change because gesture callbacks are currently sync. A smaller first step is to
inject a `spawn` function into action factories:

```python
def create_volume_action(player: PlayerBackend, state: PlayerState, spawn: SpawnFunc) -> Callable[[], None]:
    def action() -> None:
        state.volume = next_volume(state.volume)
        spawn(player.set_volume(state.volume), "set-volume")
    return action
```

---

## 4.2 Move blocking subprocess calls off the event loop

### Problem

`subprocess.run()` in menu actions blocks the loop.

### Target design

Use async subprocess helpers or `asyncio.to_thread()` for existing sync helpers.

### Async network info snippet

```python
async def get_network_info_async() -> str:
    lines = ["=== Network Info ===", ""]
    lines.append(f"Hostname: {socket.gethostname()}")

    try:
        proc = await asyncio.create_subprocess_exec(
            "ip", "-4", "addr", "show",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
    except Exception as exc:
        logger.debug("Could not get network info: %s", exc)
        return "\n".join(lines)

    if proc.returncode == 0:
        for line in stdout.decode().splitlines():
            if "inet " in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    lines.append(f"IP: {parts[1]}")

    return "\n".join(lines)
```

Action:

```python
def create_network_info_action(player: PlayerBackend, osd_duration_ms: int, spawn: SpawnFunc):
    async def run() -> None:
        info = await get_network_info_async()
        logger.info("Network info: %s", info)
        await player.show_osd(info, osd_duration_ms)

    def action() -> None:
        spawn(run(), "network-info")

    return action
```

### Reboot/shutdown snippet

```python
async def run_system_command(*args: str) -> None:
    proc = await asyncio.create_subprocess_exec(*args)
    await proc.wait()


def create_reboot_action(spawn: SpawnFunc) -> Callable[[], None]:
    def action() -> None:
        logger.info("Rebooting system")
        spawn(run_system_command("sudo", "reboot"), "reboot")
    return action
```

---

# Phase 5 — Config, state, and documented behavior

## 5.1 Add config validation

### Problem

Invalid TOML values are accepted and fail later obscurely.

### Target design

- Add `ConfigError(ValueError)`.
- Validate after loading.
- Enforce ranges/enums/types.
- Validate timing relationships.

### Planned snippet

```python
class ConfigError(ValueError):
    """Invalid MLOOP configuration."""


def validate_config(config: Config) -> None:
    if config.player.backend not in {"mpv", "cvlc"}:
        raise ConfigError("player.backend must be 'mpv' or 'cvlc'")

    if not 0 <= config.playback.volume <= 100:
        raise ConfigError("playback.volume must be between 0 and 100")

    if config.display.rotation not in {0, 90, 180, 270}:
        raise ConfigError("display.rotation must be one of 0, 90, 180, 270")

    if config.audio.output not in {"auto", "hdmi", "system-default"}:
        raise ConfigError("audio.output must be one of auto, hdmi, system-default")

    g = config.hdmi_gestures
    if g.debounce_ms >= g.cycle_min_disconnect_ms:
        raise ConfigError("hdmi_gestures.debounce_ms must be less than cycle_min_disconnect_ms")
    if g.cycle_min_disconnect_ms > g.cycle_max_disconnect_ms:
        raise ConfigError("cycle_min_disconnect_ms must be <= cycle_max_disconnect_ms")
    if g.enter_min_disconnect_ms > g.enter_max_disconnect_ms:
        raise ConfigError("enter_min_disconnect_ms must be <= enter_max_disconnect_ms")
```

Call from `load_config()`:

```python
config = Config(...)
validate_config(config)
return config
```

### Test snippet

```python
@pytest.mark.parametrize("rotation", [45, -90, 360])
def test_invalid_rotation_rejected(tmp_path, rotation):
    path = tmp_path / "config.toml"
    path.write_text(f"[display]\nrotation = {rotation}\n")
    with pytest.raises(ConfigError, match="display.rotation"):
        load_config(path)
```

---

## 5.2 Decide and implement state persistence

### Problem

`load_state()`/`save_state()` exist and docs promise runtime state, but nothing uses them.

### Option A — Implement persistence

Recommended if menu changes should survive reboot.

#### State model snippet

```python
@dataclass
class RuntimeState:
    volume: int
    rotation: int
    audio_output: str

    @classmethod
    def from_config_and_state(cls, config: Config, data: dict[str, Any]) -> RuntimeState:
        return cls(
            volume=int(data.get("volume", config.playback.volume)),
            rotation=int(data.get("rotation", config.display.rotation)),
            audio_output=str(data.get("audio_output", config.audio.output)),
        )
```

#### Save-on-change snippet

```python
def _save_runtime_state(self) -> None:
    save_state(
        {
            "volume": self.state.volume,
            "rotation": self.state.rotation,
            "audio_output": self.state.audio_output,
        }
    )
```

Action after mutation:

```python
state.volume = next_volume(state.volume)
spawn(player.set_volume(state.volume), "set-volume")
save_runtime_state()
```

#### TOML writer choice

Best: add `tomli-w` as a small runtime dependency.

```toml
# pyproject.toml
dependencies = ["tomli-w>=1.0"]
```

```python
import tomli_w


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    state_path = path or DEFAULT_STATE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "wb") as f:
        tomli_w.dump(state, f)
```

If zero runtime dependencies is mandatory, constrain state values to simple ints/known strings
and escape strings manually.

### Option B — Remove persistence

If persistence is not desired yet:

- remove `DEFAULT_STATE_PATH`, `load_state()`, `save_state()`,
- remove docs claiming `/var/lib/mloop/state.toml`,
- remove `StateDirectory=mloop` if not otherwise used.

### Recommendation

Implement persistence for `volume`, `rotation`, and `audio_output`; it matches kiosk expectations.

---

## 5.3 Replace single-element mutable lists with state object

### Problem

Current actions mutate lists like `self._current_volume = [80]`.

### Target design

Use `RuntimeState`/`PlayerState` dataclass and pass it to actions.

### Planned snippet

```python
def create_volume_action(
    player: PlayerBackend,
    state: RuntimeState,
    spawn: SpawnFunc,
    save_state: Callable[[], None],
) -> Callable[[], None]:
    def action() -> None:
        state.volume = state.volume + 10
        if state.volume > 100:
            state.volume = 10
        spawn(player.set_volume(state.volume), "set-volume")
        save_state()
        logger.info("Volume changed to %d", state.volume)

    return action
```

Rotation:

```python
def next_rotation(current: int) -> int:
    rotations = [0, 90, 180, 270]
    return rotations[(rotations.index(current) + 1) % len(rotations)]
```

---

## 5.4 Fix playlist loop semantics

### Problem

`build_playlist(loop=True)` duplicates the list once, while players also loop forever.
`loop=false` is ignored by player startup options.

### Target design

- `build_playlist()` should only sort/shuffle and return the actual media list.
- Looping should be backend/player behavior.

### Planned media snippet

```python
def build_playlist(files: list[Path], shuffle: bool = False) -> list[Path]:
    playlist = list(files)
    if shuffle:
        random.shuffle(playlist)
    return playlist
```

### mpv loop snippet

```python
loop_value = "inf" if self.playback_config.loop else "no"
args.append(f"--loop-playlist={loop_value}")
```

### cvlc loop snippet

```python
args = [self.config.cvlc_path, "--fullscreen", "--intf=dummy", "--no-video-title-show"]
if self.playback_config.loop:
    args.append("--loop")
```

### Test snippet

```python
def test_build_playlist_does_not_duplicate_for_loop(tmp_path):
    files = [tmp_path / "a.mp4", tmp_path / "b.mp4"]
    assert build_playlist(files, shuffle=False) == files
```

---

## 5.5 Clarify or implement display mode and web config

### Display mode options

Current `display.mode` is documented but unused.

Possible plans:

1. **Docs-only for now:** mark `display.mode` as planned/unsupported.
2. **Kernel-mode only:** document that forced mode is managed via `/boot/firmware/cmdline.txt`,
   not runtime config.
3. **Runtime KMS mode setting:** implement via DRM/KMS tooling/library. This is larger and likely
   not suitable for dependency-light v0.1.

Recommended now: remove or mark `display.mode` as roadmap in config docs unless implementing it.

### Web config options

Current `web.*` is parsed but no server exists.

Possible plans:

1. Remove `WebConfig` until there is a web server.
2. Keep but mark experimental/unimplemented in docs.
3. Implement a small read-only status server later.

Recommended now: mark as unimplemented roadmap or remove from example config to avoid confusion.

---

# Phase 6 — Backend capabilities

## 6.1 Add capability reporting to player backends

### Problem

cvlc stubs menu actions and OSD. With cvlc, users can select actions that do nothing, and the menu
itself is invisible.

### Target design

Backends advertise capabilities; menu only includes supported actions.

### Capability snippet

```python
# src/mloop/player/backend.py
@dataclass(frozen=True)
class PlayerCapabilities:
    osd: bool
    runtime_volume: bool
    runtime_rotation: bool
    runtime_audio_output: bool

class PlayerBackend(ABC):
    @property
    @abstractmethod
    def capabilities(self) -> PlayerCapabilities:
        ...
```

mpv:

```python
@property
def capabilities(self) -> PlayerCapabilities:
    return PlayerCapabilities(
        osd=True,
        runtime_volume=True,
        runtime_rotation=True,
        runtime_audio_output=True,
    )
```

cvlc:

```python
@property
def capabilities(self) -> PlayerCapabilities:
    return PlayerCapabilities(
        osd=False,
        runtime_volume=False,
        runtime_rotation=False,
        runtime_audio_output=False,
    )
```

### Menu-building snippet

```python
caps = self.player.capabilities
items = [MenuItem(label="Resume playback", action=create_resume_action())]

if caps.runtime_volume:
    items.append(MenuItem(label="Volume", action=create_volume_action(...)))
if caps.runtime_audio_output:
    items.append(MenuItem(label="Audio output", action=create_audio_output_action(...)))
if caps.runtime_rotation:
    items.append(MenuItem(label="Rotate video", action=create_rotation_action(...)))

items.append(MenuItem(label="Rescan media", action=create_rescan_action(...)))

if caps.osd:
    items.append(MenuItem(label="Show network info", action=create_network_info_action(...)))
```

### OSD fallback

If `caps.osd` is false, HDMI menu should either:

- be disabled with a clear startup log warning, or
- use an alternative overlay/control mechanism.

Immediate recommendation:

```python
if not self.player.capabilities.osd and self.config.hdmi_gestures.enabled:
    self.logger.warning(
        "HDMI menu requires OSD, but backend %s does not support it; disabling menu actions",
        self.config.player.backend,
    )
```

---

# Phase 7 — Low-level polish and maintainability

## 7.1 IPC future creation and request ID handling

### Planned snippet

```python
future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
```

```python
request_id = data.get("request_id")
if request_id is not None and request_id in self._pending_requests:
    future = self._pending_requests.pop(request_id)
    if not future.done():
        future.set_result(data)
```

Also consider failing pending requests when `_read_loop()` exits:

```python
finally:
    exc = ConnectionError("mpv IPC connection closed")
    for future in self._pending_requests.values():
        if not future.done():
            future.set_exception(exc)
    self._pending_requests.clear()
```

---

## 7.2 Batch or reduce mpv playlist IPC overhead

### Problem

`load_playlist()` sends one IPC request per file. This is fine for small libraries but slow for
large ones.

### Options

1. Keep as-is until performance data says otherwise.
2. Generate an M3U playlist file and load it once.
3. Use mpv `loadlist` command if available in target mpv version.

### Possible snippet

```python
async def load_playlist(self, files: list[Path]) -> None:
    playlist_path = Path(self.config.ipc_socket).with_suffix(".m3u")
    playlist_path.write_text("\n".join(str(path) for path in files) + "\n")

    ipc = await self.connect_ipc()
    await ipc.command("loadlist", str(playlist_path), "replace")
```

Before implementing, verify target mpv version supports `loadlist` as expected.

---

## 7.3 Improve platform detection

### Problem

`PlatformInfo.is_raspberry_pi` treats any `arm`/`aarch64` as Raspberry Pi.

### Planned snippet

```python
def _read_pi_model() -> str | None:
    model_path = Path("/proc/device-tree/model")
    try:
        return model_path.read_text(errors="ignore").strip("\x00\n")
    except OSError:
        return None

@dataclass
class PlatformInfo:
    ...
    device_model: str | None = None

    @property
    def is_raspberry_pi(self) -> bool:
        return self.device_model is not None and "Raspberry Pi" in self.device_model
```

---

## 7.4 Fix installer path assumptions

### Problem

`packaging/install.sh` computes `PROJECT_ROOT` but later copies files with relative paths.

### Planned snippet

```bash
cp "$PROJECT_ROOT/config/mloop.example.toml" /etc/mloop/config.toml
cp "$PROJECT_ROOT/packaging/systemd/mloop.service" /etc/systemd/system/
```

Also consider:

```bash
install -o mloop -g mloop -d /home/mloop/media /var/lib/mloop
install -d /etc/mloop /opt/mloop/src
```

---

## 7.5 Type/export polish

### Planned snippets

```python
# src/mloop/player/__init__.py
from mloop.config import PlayerConfig


def create_player(config: PlayerConfig) -> PlayerBackend:
    ...
```

```python
# src/mloop/menu/actions.py
from collections.abc import Callable, Coroutine
from typing import Any

Action = Callable[[], None]
SpawnFunc = Callable[[Coroutine[Any, Any, Any], str], None]
```

Add `py.typed` if publishing typed package:

```text
src/mloop/py.typed
```

Setuptools package data:

```toml
[tool.setuptools.package-data]
mloop = ["py.typed"]
```

---

# Documentation updates to make alongside code changes

## README.md

- State that `mloopd` is the supported command after the entrypoint fix.
- Clarify which config fields are implemented.
- If cvlc remains limited, document it as playback-only/no OSD.

## docs/configuration.md

- Add validation rules.
- Remove or mark unimplemented fields.
- Document persistence behavior if implemented.
- Update default `debounce_ms` if changed.

## docs/media.md

- Correct image duration once implemented through mpv.
- Clarify loop behavior after playlist semantics are fixed.

## docs/hdmi-gestures.md

- Update debounce defaults and recommended timing ranges.
- Add troubleshooting advice for displays/cables that bounce or do not report hotplug reliably.

## docs/audio.md

- Clarify supported audio outputs and how `audio.output` maps to mpv `audio-device`.
- If `list_audio_devices()` becomes user-facing, document the menu behavior.

---

# Consolidated regression test checklist

## Entrypoint

- `main` is not a coroutine function.
- `python -m mloop` and console script share the same path.

## Player lifecycle

- Crash recovery calls reset/start/load/apply in order.
- mpv IPC is reconnected after process replacement.
- cvlc reloads files after process replacement.
- stop timeout catches `subprocess.TimeoutExpired` and sends SIGKILL.

## Config behavior

- Invalid backend rejected.
- Invalid volume rejected.
- Invalid rotation rejected.
- Invalid gesture timing rejected.
- `image_duration_seconds` appears in mpv args.
- `loop=false` changes mpv/cvlc args.

## Menu/gestures

- Exactly one menu controller callback after daemon setup.
- 300 ms navigation gesture emits `NEXT_ITEM` at state-machine level.
- Watcher emits both edges for quick valid cycles with default timing.
- Menu state closes on timeout and does not drift.

## Async tasks

- Background task exceptions are logged.
- IPC read-loop task is retained and cancelled on disconnect.
- Pending IPC requests fail if read-loop exits.

## Persistence

- Runtime state loads from TOML.
- Volume/rotation/audio changes save state.
- Strings in state are valid TOML after save/load roundtrip.

## Backend capabilities

- mpv menu includes runtime controls.
- cvlc menu hides unsupported controls or logs a clear warning.

## Installer

- `packaging/install.sh` works when run from outside repository root.

---

# Suggested pull request breakdown

## PR 1 — Entrypoint and lint

- Fix `__main__.py` wrapper.
- Remove unused import.
- Add entrypoint unit test.
- Confirm ruff and pytest pass.

## PR 2 — Player stop/recovery

- Add `reset_after_exit()`.
- Fix `TimeoutExpired` handling.
- Reload playlist after restart.
- Add backoff and tests.

## PR 3 — Config application

- Introduce runtime state dataclass.
- Apply volume/rotation/audio on startup.
- Wire image duration and loop into player startup.
- Fix playlist duplication.

## PR 4 — Menu and gesture fixes

- Single menu controller registration.
- Lower/validate debounce.
- Add watcher-level quick-cycle tests.

## PR 5 — Async supervision

- Add daemon task supervisor.
- Retain IPC read-loop task.
- Convert blocking menu subprocess actions to async.

## PR 6 — Persistence and validation

- Add `ConfigError` + validation.
- Implement or remove state persistence.
- Update docs.

## PR 7 — Capabilities and polish

- Add backend capabilities.
- Hide unsupported cvlc controls.
- Installer path fixes.
- Type annotations, `py.typed`, optional mypy CI.

---

# Risk notes

- Changing debounce defaults can affect real hardware differently. Validate on target Pi/display/cable combinations.
- Applying `audio-device` can fail if the configured output is not available. Handle failure with a warning and fallback to `auto`.
- Adding `tomli-w` breaks the current zero-runtime-dependency posture. Decide explicitly before adding it.
- `asyncio` task supervision may surface previously hidden exceptions. Treat that as good signal, but expect tests to need updates.
- cvlc OSD/menu limitations may require product decisions, not just code changes.
