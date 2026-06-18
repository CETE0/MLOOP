# MLOOP Code Review

**Date:** 2026-06-16  
**Reviewer:** Automated architecture & code-quality review, re-verified against code and upstream docs  
**Scope:** Full `src/mloop` package, packaging, CI, docs/configuration  
**Commit reviewed:** `f6418f2` (branch `main`)

---

## Verification update

This pass re-checked the prior review against the repository and upstream documentation.
Corrections to the earlier document:

- Source size is **2,268 Python LOC under `src/mloop`**, not ~2,800.
- The local test suite currently reports **64 passed**, not 75:
  `./.venv/bin/python -m pytest -q`.
- The installed/generated `mloopd` wrapper exits with **status 1**, not status 0, because
  the wrapper calls `sys.exit(main())` and `main()` returns a coroutine object. It still
  does not run the daemon.
- CI hygiene exists in intent, but current head is not actually green locally:
  `ruff check .` fails on an unused import in `src/mloop/__main__.py`.
- The debounce finding was refined: a 300-500 ms quick cycle is not always swallowed;
  it is swallowed when the entire cycle occurs inside the debounce window from the
  previous emitted event or between poll samples, and otherwise its duration can be
  delayed/inflated by debounce + polling.

Documentation checked:

- Setuptools console scripts are wrappers equivalent to `sys.exit(function())`.
- Python `asyncio` docs state that calling a coroutine does not schedule/run it, and
  that `create_task()` tasks need a retained strong reference.
- Python `subprocess.run()` waits for completion and raises `subprocess.TimeoutExpired`.
- TOML v1.0 requires proper escaping for basic strings.
- mpv docs define `--image-display-duration=<seconds|inf>` with default **5 seconds**
  and `--loop-playlist=inf` for infinite playlist looping.
- systemd `Restart=always` restarts services after clean and unclean exits; `RestartSec=`
  controls the delay.

---

## Executive Summary

MLOOP has a clean, readable structure: display, gestures, menu, player, system, and
configuration are separated well; fake-sysfs fixtures make the HDMI path testable; and
there is a meaningful test suite.

However, the production entry point is still a **critical ship-blocker**: the packaged
`mloopd` command invokes an async coroutine synchronously, so the daemon never starts.
Beyond that, several verified issues would break or degrade field behavior even after the
entry point is fixed: player crash recovery restarts without reloading media and keeps stale
IPC state, documented startup configuration values are not applied, quick HDMI gestures can
be lost by the debounce/polling implementation, blocking subprocess calls run on the event
loop, and background tasks are unsupervised.

| Severity | Count |
|----------|-------|
| 🔴 Critical | 1 |
| 🟠 High | 8 |
| 🟡 Medium | 8 |
| 🔵 Low / polish | 7 |

---

## 🔴 Critical

### C1. `mloopd` never starts the daemon (production is dead-on-arrival)

`src/mloop/__main__.py` defines `main()` as an async coroutine:

```python
async def main() -> None:
    ...
    await daemon.run()

if __name__ == "__main__":
    asyncio.run(main())
```

But packaging points the console script directly at that coroutine:

```toml
[project.scripts]
mloopd = "mloop.__main__:main"
```

The generated wrapper in `.venv/bin/mloopd` is:

```python
from mloop.__main__ import main
sys.exit(main())
```

Setuptools documents console scripts as synchronous wrappers around the target function.
Python documents that simply calling a coroutine returns a coroutine object and does not run
it. Verified locally:

```text
$ ./.venv/bin/python - <<'PY'
import inspect
from mloop.__main__ import main
print(inspect.iscoroutinefunction(main))
print(type(main()).__name__)
PY
True
coroutine

$ ./.venv/bin/mloopd
<coroutine object main at ...>
RuntimeWarning: coroutine 'main' was never awaited
# exits 1
```

**Impact:** the installed service never starts playback. With `Restart=always` and
`RestartSec=2`, systemd will repeatedly restart the failing command.

**Why development missed it:** `scripts/dev-run.sh` uses `python -m mloop`, which hits the
working `asyncio.run(main())` path. Tests do not exercise the console script.

**Fix:** split the coroutine body from a synchronous console-script wrapper:

```python
async def _amain() -> None:
    ...

def main() -> None:
    asyncio.run(_amain())

if __name__ == "__main__":
    main()
```

Add a smoke test asserting `not inspect.iscoroutinefunction(main)` and a fast CI test that
runs the installed `mloopd` entry point through a help/dry-run path.

---

## 🟠 High

### H1. Player crash recovery loses playback state, keeps stale IPC, and has no backoff

`Daemon._run_main_loop()` restarts the process only:

```python
if not self.player.is_running:
    self.logger.warning("mpv exited unexpectedly, restarting")
    self.player.start()
```

For mpv, `start()` launches `--idle=yes` but does not reload the playlist. It also does not
clear `self._ipc`, so after a process crash the `MpvPlayer` can retain a client connected to
the dead socket/process. Even if `_load_media()` were called after restart, it could reuse the
stale IPC client instead of reconnecting.

For cvlc, `start()` launches cvlc with no file arguments; `load_playlist()` is the method that
restarts cvlc with media files. The same crash-recovery path therefore restarts empty playback.

There is also no backoff. A missing player binary or repeated launch failure can hot-loop on
the 100 ms main-loop tick. The warning is backend-hardcoded as `mpv` despite the cvlc backend.

**Fix:** on unexpected exit, disconnect/reset player IPC state, restart, then reload media and
reapply runtime settings. Add bounded exponential backoff and a failure threshold.

### H2. Duplicate/stale menu controller receives every gesture intent

`Daemon.__init__()` creates an empty `MenuModel`/`MenuController`. `run()` then calls
`_setup_gesture_handlers()`, registering controller #1. Immediately after, `_build_menu()`
creates a new model/controller and registers controller #2:

```python
self.gesture_machine.on_intent(self.menu_controller.handle_intent)  # #1
...
self.menu_model = MenuModel(items)
self.menu_controller = MenuController(self.menu_model, self.config.menu)
self.gesture_machine.on_intent(self.menu_controller.handle_intent)  # #2
```

`GestureStateMachine.on_intent()` only appends. Verified: after the normal setup sequence,
`len(daemon.gesture_machine._callbacks) == 2`.

**Impact:** every intent is delivered to both controllers. The first controller mutates a
discarded empty menu model and logs spurious open/close activity; the second controller handles
the real menu.

**Fix:** build the menu once and register exactly one callback. If menu rebuilds are planned,
add replace/clear semantics for gesture callbacks.

### H3. Documented startup config values are not applied

Several configuration fields are parsed and documented but not wired into playback startup:

- `playback.volume` is never passed to mpv/cvlc and never applied after player start.
- `display.rotation` initializes the menu's mutable list but is never applied to the player.
- `audio.output` is ignored; the menu hardcodes `['auto', 'hdmi']`.
- `playback.image_duration_seconds` is never passed as mpv `--image-display-duration`; mpv's
  documented default is 5 seconds, while MLOOP docs promise 10 seconds.
- `playback.loop = false` is ignored by both backends: mpv always starts with
  `--loop-playlist=inf`, and cvlc always starts with `--loop`.
- `display.mode` is documented but no code sets a display mode.
- `web.*` is parsed/documented but no web server exists.

**Impact:** user-facing configuration and documentation are unreliable. A kiosk operator can
set volume, rotation, image duration, or loop behavior and see no effect.

**Fix:** either implement these fields or remove/mark them as roadmap. At minimum, apply
volume/rotation/audio/image-duration/loop during startup and after player restarts.

### H4. HDMI debounce/polling can drop quick gestures and distort timing

Defaults conflict with the documented navigation gesture:

```python
cycle_min_disconnect_ms = 300
debounce_ms = 500
poll_interval_ms = 200
```

`HdmiWatcher` updates `_last_state` only when a change survives debounce. If a full
disconnect/reconnect cycle happens before debounce allows either edge to emit, the watcher sees
only the original state and emits nothing. If the disconnect edge emits but reconnect occurs
within the next debounce window, the reconnect event is delayed until a later poll, inflating
the measured disconnect duration.

Verified with a fake connector:

- previous emitted state at `t=0`; disconnect at `t=100`, reconnect at `t=400`;
  polls at 200/400/600 => **no events emitted**.
- disconnect at `t=600`, reconnect at `t=900`; polls at 600/800/1000/1200 => events at
  600 and 1200, so a real 300 ms cycle is reported as 600 ms.

**Fix:** make debounce shorter than the minimum valid gesture (e.g. 100-150 ms), or implement
edge stabilization separately from gesture timing. Add watcher-level tests for quick cycles,
not just state-machine tests with ideal timestamps.

### H5. Blocking subprocess calls run on the asyncio event loop

The daemon is a single-threaded asyncio application, but menu actions call blocking helpers:

- `get_network_info()` runs `subprocess.run(['ip', ...], timeout=5)`.
- reboot/shutdown actions call synchronous `subprocess.run()`.
- `drm.get_kmsprint_connectors()` and `audio.devices.list_audio_devices()` also use blocking
  `subprocess.run()` if called from async paths later.

Python documents `subprocess.run()` as waiting for the command to complete. While a menu action
is running it, HDMI polling, OSD updates, player IPC, and timeout checks can be stalled.

**Fix:** use `asyncio.create_subprocess_exec()` or `asyncio.to_thread()`/`run_in_executor()`
for subprocess work triggered by intents.

### H6. Fire-and-forget tasks are unsupervised and may disappear or hide errors

Examples:

- `menu/actions.py` uses `asyncio.create_task(...)` for volume, rotation, audio output, rescan,
  and OSD calls.
- `daemon._on_hdmi_event()` creates an OSD task without retaining it.
- `MpvIpcClient.connect()` starts `_read_loop()` without storing the task.

Python docs explicitly warn to save a reference to tasks because the event loop only keeps weak
references. Exceptions from these tasks are also not observed by application code.

The IPC read loop is especially important: if it exits or is collected, pending requests hang
until their timeout and future IPC may become unreliable.

**Fix:** keep long-lived tasks on `self`, keep short-lived background tasks in a supervised set,
remove them on completion, and log/handle exceptions in done callbacks.

### H7. Player `stop()` catches the wrong timeout exception

Both `MpvPlayer.stop()` and `CvlcPlayer.stop()` use:

```python
try:
    os.killpg(..., signal.SIGTERM)
    self._process.wait(timeout=5)
except (ProcessLookupError, TimeoutError):
    ... SIGKILL ...
```

`subprocess.Popen.wait(timeout=...)` raises `subprocess.TimeoutExpired`, not built-in
`TimeoutError`. A hung player process therefore causes `stop()` to raise instead of escalating
to SIGKILL and cleaning up state.

**Fix:** catch `subprocess.TimeoutExpired` and then send SIGKILL to the process group.

### H8. Current lint/type quality gates are not green or not enforced

Local checks on this commit:

```text
./.venv/bin/python -m ruff check .
# F401 `mloop.config.Config` imported but unused in src/mloop/__main__.py

./.venv/bin/python -m mypy src/mloop
# src/mloop/config.py:116: "type" has no attribute "__dataclass_fields__"
```

CI runs ruff and pytest but not mypy. `mypy>=1.0` is listed as a dev dependency without a
configuration or CI job.

**Fix:** remove the unused import, add/curate mypy config, and run mypy in CI if it remains a
dev dependency.

---

## 🟡 Medium

### M1. State persistence is dead code and docs overpromise it

`DEFAULT_STATE_PATH`, `load_state()`, and `save_state()` exist, and docs say
`/var/lib/mloop/state.toml` is runtime state modified by menu actions. No production code calls
these functions. Menu changes to volume, rotation, and audio output are lost on restart.

### M2. Hand-written TOML writer is fragile

`save_state()` manually writes TOML. Strings are not escaped, so quotes/backslashes/newlines can
produce invalid TOML. The fallback branch uses Python `repr`, which is not a TOML serializer for
many types. Use `tomli-w` or constrain state values and escape according to TOML rules.

### M3. cvlc backend exposes menu features it cannot perform

`CvlcPlayer.set_volume()`, `set_rotation()`, `set_audio_output()`, and `show_osd()` are stubs.
With `backend = "cvlc"`, the menu appears functional but most actions do nothing, and OSD menu
rendering is invisible.

Add backend capability flags and hide/disable unsupported menu items, or document cvlc as
playback-only.

### M4. No config validation or type coercion

`load_config()` trusts TOML values. Examples that are accepted until later failure:

- `volume = 999`
- `rotation = 45`
- `backend = "mpvv"`
- wrong scalar/list types
- inconsistent timing such as `debounce_ms >= cycle_min_disconnect_ms`

Add range/enum/type validation at load time with actionable errors.

### M5. Two sources of truth for whether the menu is open

`GestureStateMachine` has `MENU_OPEN`/`SELECTING`, while `MenuModel` has `_open`.
`daemon._on_hdmi_event()` reads `self.menu_model.is_open`. The two can desynchronize across
timeouts, duplicate callbacks, or future rebuilds.

Prefer one authority or explicit synchronization assertions.

### M6. Shared mutable state is threaded through single-element lists

`Daemon` uses `self._current_volume = [80]`, `self._current_rotation = [...]`, and
`self._current_audio_idx = [0]` so closures can mutate values. This is hard to read and easy to
desynchronize from persisted/configured state.

Use a small `PlayerState` dataclass and persist it if M1 is implemented.

### M7. Playlist looping is implemented twice and inconsistently

`build_playlist(loop=True)` duplicates the playlist once, while mpv is always launched with
`--loop-playlist=inf` and cvlc with `--loop`. If a backend did not loop, `build_playlist()` would
only play the list twice, not indefinitely; with current backends it is redundant, and
`loop=false` is ignored by the player process.

### M8. Installer assumes current working directory

`packaging/install.sh` computes `PROJECT_ROOT` but later copies `config/mloop.example.toml` and
`packaging/systemd/mloop.service` using relative paths. Running the script from outside the
repository root can fail. Use `$PROJECT_ROOT/config/...` and `$PROJECT_ROOT/packaging/...`.

---

## 🔵 Low / Polish

- **L1.** `asyncio.get_event_loop().create_future()` in `MpvIpcClient._send_command()` should use
  `asyncio.get_running_loop().create_future()` in coroutine context.
- **L2.** `if request_id and request_id in self._pending_requests` drops a valid response with
  `request_id == 0`. IDs start at 1 today, but `is not None` is safer.
- **L3.** `MpvPlayer.load_playlist()` sends one IPC round-trip per file. Fine for small libraries,
  but O(n) IPC latency for large media directories.
- **L4.** `Daemon.run()` calls `get_platform_info()` only for logging side effects and always logs
  `"Config loaded from defaults"`, even when a config file was loaded.
- **L5.** `_parse_section(data, cls, defaults)` always receives the same class for `cls` and
  `defaults`; the `defaults` parameter is redundant.
- **L6.** `__main__` config loading is redundant:
  `load_config(config_path) if config_path else load_config()` can be `load_config(config_path)`.
- **L7.** Type/export polish: `create_player(config)` is untyped; action factories return `Any`;
  there is no `py.typed` marker.

---

## ✅ What's done well

- Clean module boundaries: display, gestures, menu, player, system, audio, and config are cohesive.
- Player abstraction is real (`PlayerBackend` + factory), so backend fixes are localized.
- Dependency-light runtime footprint is appropriate for a Raspberry Pi appliance.
- HDMI testing is approachable via fake sysfs roots and injected monotonic timestamps.
- Process groups (`start_new_session` + `killpg`) are the right design for player cleanup once
  the timeout exception bug is fixed.
- Docs are broad and useful, even where they currently run ahead of implementation.

---

## Recommended priority order

1. **C1** — fix the synchronous `mloopd` entry point and add a console-script smoke test.
2. **H1/H7** — make player restart/stop robust: reset IPC, reload media, reapply settings, catch
   `subprocess.TimeoutExpired`, and add restart backoff.
3. **H2** — register exactly one menu controller.
4. **H3/H4** — make documented config and HDMI gesture timings match actual behavior.
5. **H5/H6** — remove blocking work from the event loop and supervise background tasks.
6. **H8** — restore green ruff, decide whether mypy is required, and enforce it if so.
7. **M1/M2** — either implement state persistence safely or remove the dead API/docs.

---

## Suggested regression tests to add

- Console entry point is synchronous: `not inspect.iscoroutinefunction(mloop.__main__.main)`.
- Generated/installed `mloopd` can execute a fast dry-run/help path without returning a coroutine.
- Player crash path reloads playlist and reconnects IPC after restart.
- Hung `Popen.wait(timeout=...)` triggers SIGKILL escalation.
- Normal daemon setup registers exactly one gesture intent callback.
- Watcher-level quick-cycle tests around debounce and 200 ms polling.
- Startup applies configured volume, rotation, audio output, image duration, and loop behavior.
- Invalid config values fail fast with clear errors.
