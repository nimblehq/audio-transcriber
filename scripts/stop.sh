#!/bin/bash
#
# stop.sh — terminate the background uvicorn server started by launch.sh.
#
# Bounded teardown: SIGTERM, wait up to ~2s, then SIGKILL. Kept fast so it can
# finish inside the logout quit-reply window. Idempotent — safe to run when the
# server is already gone.

set -u

LOG_FILE="$HOME/Library/Logs/MeetingTranscriber.log"
PID_FILE="$HOME/Library/Application Support/MeetingTranscriber/uvicorn.pid"

log() {
  printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$LOG_FILE" 2>/dev/null
}

[ -f "$PID_FILE" ] || exit 0
pid="$(cat "$PID_FILE" 2>/dev/null)"

if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
  log "Stopping server (PID $pid)..."
  kill -TERM "$pid" 2>/dev/null
  for _ in 1 2 3 4; do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.5
  done
  if kill -0 "$pid" 2>/dev/null; then
    log "Server did not exit; sending SIGKILL."
    kill -KILL "$pid" 2>/dev/null
  fi
  log "Server stopped."
fi

rm -f "$PID_FILE"
