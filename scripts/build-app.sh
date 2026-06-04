#!/bin/bash
#
# build-app.sh — build "dist/Meeting Transcriber.app" from launcher.applescript.
#
# Uses osacompile (ships with macOS), so there is no extra build dependency.
# The absolute repo path is baked into the app at build time; move the repo and
# rebuild. The built .app is gitignored — this script is the committed artifact.

set -euo pipefail

if [ "$(uname)" != "Darwin" ]; then
  echo "build-app.sh requires macOS (osacompile)." >&2
  exit 1
fi
if ! command -v osacompile >/dev/null 2>&1; then
  echo "osacompile not found (expected on macOS)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
if git -C "$REPO_ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git -C "$REPO_ROOT" rev-parse --show-toplevel)"
fi

SRC="$REPO_ROOT/scripts/launcher.applescript"
DIST="$REPO_ROOT/dist"
APP="$DIST/Meeting Transcriber.app"
ICON="$REPO_ROOT/assets/MeetingTranscriber.icns"

mkdir -p "$DIST"
rm -rf "$APP"

tmpdir="$(mktemp -d -t meeting-transcriber-build.XXXXXX)"
trap 'rm -rf "$tmpdir"' EXIT
tmp="$tmpdir/launcher.applescript"
# Escape characters special to sed's replacement (&, |, \) in the repo path.
escaped_root="$(printf '%s' "$REPO_ROOT" | sed -e 's/[&|\\]/\\&/g')"
sed "s|__REPO_ROOT__|$escaped_root|g" "$SRC" >"$tmp"

osacompile -o "$APP" "$tmp"

if [ -f "$ICON" ]; then
  cp "$ICON" "$APP/Contents/Resources/applet.icns"
  echo "Applied custom icon."
fi

echo "Built: $APP"
echo
echo "Next steps:"
echo "  1. Drag \"$APP\" to /Applications or your Dock."
echo "  2. First launch: right-click the app and choose Open to clear Gatekeeper."
echo "  3. Double-click to start. Quit (Cmd-Q) to stop the server."
