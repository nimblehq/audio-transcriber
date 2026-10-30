from __future__ import annotations

from pathlib import Path

import pytest

from backend.services import changelog

SAMPLE = """# Changelog

Some preamble text.

## [Unreleased]

### Fixed

- An unreleased fix that must never surface in the app.

## [1.2.0] - 2026-05-08

### Added

- First feature.
- A multi-line bullet that wraps onto
  a continuation line.

### Fixed

- A bug fix.

## [1.1.0] - 2026-02-26

### Changed

- A single change.
"""


@pytest.fixture
def changelog_file(tmp_path: Path, monkeypatch) -> Path:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(SAMPLE, encoding="utf-8")
    monkeypatch.setattr(changelog, "CHANGELOG_PATH", path)
    return path


class TestGetChangelog:
    def test_current_version_is_latest_released(self, changelog_file):
        assert changelog.get_changelog().current_version == "1.2.0"

    def test_entries_newest_first(self, changelog_file):
        versions = [e.version for e in changelog.get_changelog().entries]
        assert versions == ["1.2.0", "1.1.0"]

    def test_unreleased_is_excluded(self, changelog_file):
        versions = [e.version for e in changelog.get_changelog().entries]
        assert "Unreleased" not in versions

    def test_sections_and_dates_parsed(self, changelog_file):
        latest = changelog.get_changelog().entries[0]
        assert latest.date == "2026-05-08"
        assert list(latest.sections) == ["Added", "Fixed"]
        assert latest.sections["Fixed"] == ["A bug fix."]

    def test_continuation_lines_join_bullet(self, changelog_file):
        added = changelog.get_changelog().entries[0].sections["Added"]
        assert added[0] == "First feature."
        assert added[1] == "A multi-line bullet that wraps onto a continuation line."

    def test_missing_file_degrades_to_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(changelog, "CHANGELOG_PATH", tmp_path / "nope.md")
        result = changelog.get_changelog()
        assert result.current_version is None
        assert result.entries == []

    def test_only_unreleased_yields_no_current_version(self, tmp_path, monkeypatch):
        path = tmp_path / "CHANGELOG.md"
        path.write_text("# Changelog\n\n## [Unreleased]\n\n### Fixed\n\n- wip\n", encoding="utf-8")
        monkeypatch.setattr(changelog, "CHANGELOG_PATH", path)
        result = changelog.get_changelog()
        assert result.current_version is None
        assert result.entries == []

    def test_empty_sections_are_dropped(self, tmp_path, monkeypatch):
        path = tmp_path / "CHANGELOG.md"
        path.write_text(
            "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n### Added\n\n### Fixed\n\n- real\n", encoding="utf-8"
        )
        monkeypatch.setattr(changelog, "CHANGELOG_PATH", path)
        entry = changelog.get_changelog().entries[0]
        assert "Added" not in entry.sections
        assert entry.sections["Fixed"] == ["real"]
