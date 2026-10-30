from __future__ import annotations

from pathlib import Path

from backend.services import changelog


class TestGetChangelog:
    async def test_returns_structured_entries(self, client, tmp_path: Path, monkeypatch):
        path = tmp_path / "CHANGELOG.md"
        path.write_text(
            "# Changelog\n\n## [2.0.0] - 2026-06-01\n\n### Added\n\n- A shipped feature.\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(changelog, "CHANGELOG_PATH", path)

        res = await client.get("/api/changelog")

        assert res.status_code == 200
        body = res.json()
        assert body["current_version"] == "2.0.0"
        assert body["entries"][0]["sections"]["Added"] == ["A shipped feature."]

    async def test_missing_changelog_returns_200_empty(self, client, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(changelog, "CHANGELOG_PATH", tmp_path / "nope.md")

        res = await client.get("/api/changelog")

        assert res.status_code == 200
        assert res.json() == {"current_version": None, "entries": []}
