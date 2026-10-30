"""Parse the hand-maintained ``CHANGELOG.md`` into structured release entries.

The changelog follows the Keep a Changelog format: released versions are
``## [x.y.z] - date`` headings, each grouping change bullets under
``### Section`` sub-headings (Added / Changed / Fixed / ...). The ``[Unreleased]``
section is skipped — only shipped releases are surfaced in the app. The latest
released heading is treated as the current app version (see #155).
"""

from __future__ import annotations

import re

from backend.schemas import ChangelogEntry, ChangelogResponse
from config import CHANGELOG_PATH

# ``## [1.2.0] - 2026-05-08`` or ``## [Unreleased]`` (date optional).
_VERSION_RE = re.compile(r"^##\s+\[(?P<version>[^\]]+)\](?:\s*-\s*(?P<date>.+))?\s*$")
# ``### Added`` / ``### Fixed`` / ...
_SECTION_RE = re.compile(r"^###\s+(?P<name>.+?)\s*$")
# ``- a change`` (two-space or tab continuation lines belong to the prior bullet).
_BULLET_RE = re.compile(r"^-\s+(?P<text>.*)$")
_CONTINUATION_RE = re.compile(r"^\s+(?P<text>\S.*)$")


def _parse(text: str) -> list[ChangelogEntry]:
    """Parse changelog markdown into released entries, newest first."""
    entries: list[ChangelogEntry] = []
    entry: ChangelogEntry | None = None
    section: str | None = None
    bullets: list[str] | None = None

    def flush_bullet(line: str) -> None:
        # Append a continuation line to the last bullet in the current section.
        if bullets:
            bullets[-1] = f"{bullets[-1]} {line.strip()}"

    for line in text.splitlines():
        version_match = _VERSION_RE.match(line)
        if version_match:
            version = version_match.group("version").strip()
            if version.lower() == "unreleased":
                entry = None  # Skip the Unreleased section entirely.
                section = None
                bullets = None
                continue
            date = (version_match.group("date") or "").strip() or None
            entry = ChangelogEntry(version=version, date=date, sections={})
            entries.append(entry)
            section = None
            bullets = None
            continue

        if entry is None:
            continue  # Preamble, or inside Unreleased.

        section_match = _SECTION_RE.match(line)
        if section_match:
            section = section_match.group("name").strip()
            bullets = entry.sections.setdefault(section, [])
            continue

        if section is None or bullets is None:
            continue

        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            bullets.append(bullet_match.group("text").strip())
            continue

        if _CONTINUATION_RE.match(line) and bullets:
            flush_bullet(line)

    # Drop sections that ended up with no bullets.
    for e in entries:
        e.sections = {name: items for name, items in e.sections.items() if items}
    return entries


def get_changelog() -> ChangelogResponse:
    """Return released changelog entries and the current (latest) version.

    Missing or empty changelog degrades to an empty response (no error) so the
    optional "What's new" feature simply shows nothing.
    """
    if not CHANGELOG_PATH.exists():
        return ChangelogResponse(current_version=None, entries=[])

    entries = _parse(CHANGELOG_PATH.read_text(encoding="utf-8"))
    current_version = entries[0].version if entries else None
    return ChangelogResponse(current_version=current_version, entries=entries)
