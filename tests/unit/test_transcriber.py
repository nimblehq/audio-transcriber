from __future__ import annotations

import json
from pathlib import Path

from backend.services.transcriber import _is_cancelled


class TestIsCancelled:
    def test_returns_false_when_processing(self, tmp_path: Path):
        meta = {"id": "m1", "title": "Test", "status": "processing", "audio_filename": "a.wav"}
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps(meta))

        assert _is_cancelled(meta_path) is False

    def test_returns_true_when_error(self, tmp_path: Path):
        meta = {"id": "m1", "title": "Test", "status": "error", "audio_filename": "a.wav"}
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps(meta))

        assert _is_cancelled(meta_path) is True

    def test_returns_true_when_ready(self, tmp_path: Path):
        meta = {"id": "m1", "title": "Test", "status": "ready", "audio_filename": "a.wav"}
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps(meta))

        assert _is_cancelled(meta_path) is True

    def test_returns_false_on_read_error(self, tmp_path: Path):
        meta_path = tmp_path / "nonexistent.json"
        assert _is_cancelled(meta_path) is False
