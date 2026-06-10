#!/bin/bash
#
# launch.sh — start the Meeting Transcriber app from a double-click launcher.
#
# Flow: fast-forward pull -> refresh deps (venv + pip) -> start uvicorn in the
# background -> wait until it answers -> open the browser. Every failure path
# logs to ~/Library/Logs/MeetingTranscriber.log and surfaces an osascript
# dialog quoting the log path, so the user always gets a breadcrumb.
#
# Safe to run directly from a terminal as well as from the built .app.

set -u

# `do shell script` (the .app entry point) runs with a minimal PATH, so the
# tools we rely on (git, python3.12, curl, open) must be reachable. Prepend the
# common Homebrew/macOS locations.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

LOG_DIR="$HOME/Library/Logs"
LOG_FILE="$LOG_DIR/MeetingTranscriber.log"
SUPPORT_DIR="$HOME/Library/Application Support/MeetingTranscriber"
PID_FILE="$SUPPORT_DIR/uvicorn.pid"

URL="http://localhost:8000"
API_URL="$URL/api/meetings"
READY_TIMEOUT=20

mkdir -p "$LOG_DIR" "$SUPPORT_DIR"

log() {
  printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$LOG_FILE"
}

# fail <message> — log, show a dialog pointing at the log, and exit non-zero.
fail() {
  local message="$1"
  log "ERROR: $message"
  if command -v osascript >/dev/null 2>&1; then
    osascript >/dev/null 2>&1 <<OSA || true
display dialog "Meeting Transcriber could not start.

$message

See the log for details:
$LOG_FILE" buttons {"OK"} default button "OK" with title "Meeting Transcriber" with icon caution
OSA
  fi
  exit 1
}

# probe — classify what is answering on port 8000.
# Echoes one of: "ours" | "foreign" | "down". Never fails the script.
probe() {
  local body code
  body="$(mktemp)"
  code="$(curl -s -m 3 -o "$body" -w '%{http_code}' "$API_URL" 2>/dev/null)"
  local curl_exit=$?
  if [ "$curl_exit" -ne 0 ]; then
    rm -f "$body"
    echo "down"
    return
  fi
  if [ "$code" = "200" ] && [ "$(head -c 1 "$body")" = "[" ]; then
    rm -f "$body"
    echo "ours"
    return
  fi
  rm -f "$body"
  echo "foreign"
}

open_browser() {
  log "Opening $URL"
  open "$URL" 2>>"$LOG_FILE" || true
}

log "----- launch start ($REPO_ROOT) -----"

# 1. If our app is already serving, just bring the browser forward (idempotent).
case "$(probe)" in
  ours)
    log "App already running; opening browser."
    open_browser
    exit 0
    ;;
  foreign)
    fail "Port 8000 is already in use by another process. Quit it and try again."
    ;;
esac

cd "$REPO_ROOT" || fail "Could not enter the project folder: $REPO_ROOT"

# 2. Fast-forward pull (best effort: skip when offline or not a git checkout).
if [ -d "$REPO_ROOT/.git" ] || git rev-parse --git-dir >/dev/null 2>&1; then
  log "Pulling latest changes (git pull --ff-only)..."
  if git pull --ff-only >>"$LOG_FILE" 2>&1; then
    log "Pull complete."
  else
    status=$?
    # A rejected fast-forward means local/remote diverged — that is a real
    # problem the user should know about. A network failure is not.
    if git status --porcelain=v1 -b 2>/dev/null | grep -q '\[ahead\|\[behind\|diverged'; then
      fail "Could not update the app (git pull --ff-only was rejected). Your local copy may have diverged from the remote."
    fi
    log "Pull skipped (offline or unavailable, exit $status); continuing with the local copy."
  fi
else
  log "Not a git checkout; skipping update."
fi

# 3. Ensure the virtual environment and dependencies.
VENV_PY="$REPO_ROOT/.venv/bin/python"
if [ ! -x "$VENV_PY" ]; then
  command -v python3.12 >/dev/null 2>&1 || fail "Python 3.12 is required but was not found. Run the one-time setup (see README) first."
  log "Creating virtual environment..."
  python3.12 -m venv "$REPO_ROOT/.venv" >>"$LOG_FILE" 2>&1 || fail "Could not create the Python virtual environment."
fi
log "Refreshing dependencies..."
"$VENV_PY" -m pip install -q -r "$REPO_ROOT/requirements.txt" >>"$LOG_FILE" 2>&1 || fail "Could not install Python dependencies."

# 4. Start uvicorn (no --reload, so there is a single process to terminate).
log "Starting server..."
nohup "$VENV_PY" -m uvicorn backend.main:app --host localhost --port 8000 \
  >>"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
log "Server PID $(cat "$PID_FILE")."

# 5. Wait until the server answers (connection-refused/5xx => keep waiting).
deadline=$((SECONDS + READY_TIMEOUT))
while [ "$SECONDS" -lt "$deadline" ]; do
  if [ "$(probe)" = "ours" ]; then
    log "Server is ready."
    open_browser
    log "----- launch done -----"
    exit 0
  fi
  # If the process died, stop waiting and report.
  pid="$(cat "$PID_FILE" 2>/dev/null)"
  if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
    fail "The server process exited unexpectedly during startup."
  fi
  sleep 1
done

fail "The server did not become ready within ${READY_TIMEOUT}s."
