# Plan: Wrap the app as a double-click macOS launcher

**Story**: #62
**Spec**: N/A (no spec; rough ACs in the issue)
**Branch**: feature/62-macos-double-click-launcher
**Date**: 2026-06-04
**Mode**: Standard — deliverable is shell + AppleScript glue + a build script; behavioral ACs require manual macOS verification and cannot run on the Linux CI.

## Technical Decisions

### TD-1: Build tool = `osacompile`, not Platypus
- **Context**: The issue suggests Platypus or an AppleScript droplet to wrap a shell script into a `.app`.
- **Decision**: Use `osacompile`, which ships with macOS — zero extra build dependency. Produces an AppleScript `.app`.
- **Alternatives considered**: Platypus (nicer menu-bar UX but requires `brew install platypus` at build time). Deferred as optional future enhancement.

### TD-2: App stays alive to own the uvicorn lifecycle
- **Context**: AC3 requires that closing the app cleanly terminates uvicorn, so the app must outlive the launch and supervise uvicorn.
- **Decision**: AppleScript app with `on run` (start), `on idle return 30` (stay alive, Dock presence), `on quit` (run stop.sh, then `continue quit`). AC3 ("closing the app cleanly terminates uvicorn") is dependably met for **explicit Quit** (Cmd-Q / Dock Quit). Logout/shutdown teardown is **best-effort**: macOS sends a Quit Apple Event at logout, but an osacompile `.app` running `do shell script` in `on quit` is subject to the quit-reply timeout, and uvicorn is `nohup`-detached from the launcher's process tree, so teardown depends entirely on stop.sh completing in time.
- **Alternatives considered**: Platypus status-menu app (auto process-group teardown, but extra build dep); fire-and-forget launcher that quits immediately (cannot satisfy AC3).

### TD-3: Deps refresh via venv + pip, not `uv`
- **Context**: The issue proposes `uv sync --quiet`, but this repo does not use uv.
- **Decision**: Match `make setup` exactly — ensure `.venv` exists (create with `python3.12 -m venv` if missing), then `pip install -q -r requirements.txt`.
- **Alternatives considered**: `uv sync` (issue's proposal) — rejected; repo has no `uv.lock` and uses pip.

### TD-4: uvicorn started without `--reload`, backgrounded with a pidfile
- **Context**: `run.py` runs uvicorn with `reload=True`, which spawns a watcher subprocess complicating clean teardown.
- **Decision**: Launch via `python -m uvicorn backend.main:app --host localhost --port 8000` (no reload), backgrounded with `nohup`, PID written to a pidfile under `~/Library/Application Support/MeetingTranscriber/`. `run.py` is left untouched.
- **Alternatives considered**: Reusing `run.py` (reload-on; harder to terminate cleanly).

### TD-5: Repo path resolved at build time
- **Context**: Open question — where does the repo live on disk?
- **Decision**: `build-app.sh` bakes the absolute repo root (`git rev-parse --show-toplevel`) into the generated AppleScript. Moving the repo means rebuilding. The `.app` can then live in `/Applications` or the Dock.
- **Alternatives considered**: Hard-coded `~/Applications/audio-transcription`; runtime config file. Build-time bake is simplest and unambiguous.

### TD-6: Kill (not detach) uvicorn on quit, bounded teardown
- **Context**: Open question — kill or detach a long-running transcription on quit?
- **Decision**: Kill. Job state is in-memory and not resumable; detaching would orphan uvicorn and violate AC3. `stop.sh` kills the uvicorn process group with a bounded grace: SIGTERM → wait up to 2s → SIGKILL, so it finishes within the logout quit-reply window. Idempotent; removes the pidfile.
- **Alternatives considered**: Detach and let transcription finish (orphans the server; breaks AC3).

### TD-7: Port-in-use uses an app-specific discriminator, not a bare 200
- **Context**: The SPA catch-all route returns 200 for any path, so a bare 200 on :8000 cannot distinguish "our app" from a foreign process.
- **Decision**: Probe `GET http://localhost:8000/api/meetings` (our API returns a JSON array). Three states: connection-refused/5xx → keep polling until ~20s timeout (our app booting); 200 + JSON-array shape → success (open browser; idempotent if already running); clearly-foreign 200 → `fail()` dialog "port 8000 in use by another process".
- **Alternatives considered**: Bare 200 on `/` (false positives from the SPA catch-all and from foreign processes).

### TD-8: No code signing / notarization
- **Context**: Open question — needed for distribution?
- **Decision**: Skip (single-user/internal tool). README documents the one-time Gatekeeper right-click→Open / `xattr -dr com.apple.quarantine`.
- **Alternatives considered**: Full notarization (out of scope while single-user).

### TD-9: Centralized failure handling with osascript dialogs
- **Context**: AC4 — failures must show a dialog, not silent nothing.
- **Decision**: A shared `fail()` shell function appends to `~/Library/Logs/MeetingTranscriber.log` and shows an `osascript display dialog` quoting the log path, then exits non-zero. Every failure path (git pull rejected, venv/pip error, port conflict, health timeout) routes through it. `launch.sh` owns the dialogs so they work whether invoked from the `.app` or directly.

## Files to Create or Modify

- `scripts/launch.sh` (create) — core launcher: resolve baked repo root, cd, `git pull --ff-only` (skip-with-log when offline / not a checkout), ensure venv, `pip install -q -r requirements.txt`, start uvicorn (no-reload, nohup, pidfile), poll `/api/meetings` until healthy or ~20s, `open` the URL, exit 0. Logs to `~/Library/Logs/MeetingTranscriber.log`. `fail()` helper shows osascript dialog.
- `scripts/stop.sh` (create) — read pidfile, kill uvicorn process group (TERM → 2s → KILL), remove pidfile. Idempotent.
- `scripts/launcher.applescript` (create) — `on run` → `do shell script "<repo>/scripts/launch.sh"`; `on idle return 30`; `on quit` → `do shell script "<repo>/scripts/stop.sh"`, `continue quit`. Repo path placeholder substituted at build time.
- `scripts/build-app.sh` (create) — substitute repo path into a temp copy of the AppleScript, `osacompile -o "dist/Meeting Transcriber.app"`, apply `assets/MeetingTranscriber.icns` if present (best-effort), print next-step instructions. Guards: require macOS (Darwin) and `osacompile`.
- `tests/test_launcher_scripts.py` (create) — `@pytest.mark.unit` test running `bash -n` on launch.sh and stop.sh; skips gracefully if `bash` is unavailable. Syntax guard only.
- `README.md` (modify) — add "Double-click launcher (macOS)" section, leading with the required one-time build step; notes no prebuilt `.app` is committed, pull-on-launch behavior, Gatekeeper, log path, and that quitting cancels in-progress transcription.
- `.gitignore` (modify) — add `dist/`.
- `Makefile` (modify) — add `app:` target calling `scripts/build-app.sh`.

## Approach per AC

### AC 1: A `.app` exists in the repo (or a build script that produces one)
`scripts/build-app.sh` (and a `make app` target) produce `dist/Meeting Transcriber.app` via `osacompile`. The bundle is gitignored (`dist/`); the build script is the committed artifact. README leads with this required one-time build step.

### AC 2: Double-click on a fresh checkout (after one-time setup) opens the app in the browser within ~5s
After building the `.app` once, double-click runs `launch.sh`: fast-forward pull, deps refresh (near-instant on the warm path), uvicorn boot, readiness poll on `/api/meetings`, then `open`. The ~5s target holds on the warm path (deps already satisfied); a real `pip install` exceeds it (documented).

### AC 3: Closing the app cleanly terminates uvicorn
`on quit` runs `stop.sh`, which TERMs then KILLs the uvicorn process group via the pidfile. Dependable for explicit Quit; logout/shutdown is best-effort (TD-2).

### AC 4: Failures show a dialog, not silent nothing
Every failure path routes through `fail()`, which logs and shows an `osascript display dialog` with the log path, then exits non-zero.

## Commit Sequence

1. `scripts/launch.sh` + `scripts/stop.sh`
2. `scripts/launcher.applescript` + `scripts/build-app.sh` + Makefile `app` target + `.gitignore`
3. `tests/test_launcher_scripts.py`
4. README docs

## Risks and Trade-offs

- **AC2 "~5s"** only holds on the warm path; a real `pip install` blows past it. Documented.
- **Unsigned `.app`** → Gatekeeper friction on first open. Mitigated by docs, not eliminated.
- **Logout/shutdown teardown** is best-effort — osacompile quit-reply timeout + `nohup` detachment mean uvicorn may be orphaned if `stop.sh` doesn't finish in the reply window. A LaunchAgent (RunAtLoad, KeepAlive=false) backstop that reaps a stale pidfile on next login is noted as future hardening, out of scope here.
- **Behavioral ACs unverifiable in Linux CI** → manual macOS verification is the real gate; `bash -n` is a syntax guard only.
- **Pull on every launch** couples launch to network + git state; skipped when offline / not a checkout. Documented so behavior changes between launches are expected.

## Deviations from Plan

_Populated after implementation._
