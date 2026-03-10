#!/usr/bin/env bash
# Argus Context Monitor Hook
# Tracks tool-call count as a proxy for context usage.
# Warns when approaching context limits so agents can compact at phase boundaries.

ARGUS_DIR="${ARGUS_DIR:-.argus}"
STATE_FILE="${ARGUS_DIR}/debug/.context-monitor-state"
LOG_FILE="${ARGUS_DIR}/debug/context-monitor.log"

# Configurable thresholds (tool call counts)
# These are conservative estimates based on typical context window sizes.
# Override with environment variables if needed.
MAX_TOOL_CALLS="${ARGUS_MAX_TOOL_CALLS:-150}"
WARNING_PERCENT="${ARGUS_WARNING_PERCENT:-65}"
CRITICAL_PERCENT="${ARGUS_CRITICAL_PERCENT:-75}"

WARNING_THRESHOLD=$(( MAX_TOOL_CALLS * WARNING_PERCENT / 100 ))
CRITICAL_THRESHOLD=$(( MAX_TOOL_CALLS * CRITICAL_PERCENT / 100 ))

# Ensure state directory exists
mkdir -p "$(dirname "$STATE_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

# Read or initialize counter
if [ -f "$STATE_FILE" ]; then
  COUNT=$(cat "$STATE_FILE")
else
  COUNT=0
fi

# Increment counter
COUNT=$((COUNT + 1))
echo "$COUNT" > "$STATE_FILE"

# Check thresholds
if [ "$COUNT" -ge "$CRITICAL_THRESHOLD" ]; then
  REMAINING=$(( MAX_TOOL_CALLS - COUNT ))
  echo "[ARGUS CONTEXT CRITICAL] Tool call ${COUNT}/${MAX_TOOL_CALLS} (~${REMAINING} remaining)."
  echo "Context is nearly exhausted. You should:"
  echo "  1. Commit all current progress immediately"
  echo "  2. Write a handoff to .argus/handoff.md"
  echo "  3. Suggest the user start a fresh session to continue"
  echo ""
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) CRITICAL count=${COUNT} max=${MAX_TOOL_CALLS}" >> "$LOG_FILE"
elif [ "$COUNT" -ge "$WARNING_THRESHOLD" ]; then
  REMAINING=$(( MAX_TOOL_CALLS - COUNT ))
  echo "[ARGUS CONTEXT WARNING] Tool call ${COUNT}/${MAX_TOOL_CALLS} (~${REMAINING} remaining)."
  echo "Wrap up the current sub-task and prepare for a clean stopping point."
  echo "Avoid starting new phases of work."
  echo ""
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) WARNING count=${COUNT} max=${MAX_TOOL_CALLS}" >> "$LOG_FILE"
fi
