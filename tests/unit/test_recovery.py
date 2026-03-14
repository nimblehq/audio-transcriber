from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from backend.services.recovery import recover_stuck_meetings


@pytest.fixture
def meetings_dir(tmp_path):
    d = tmp_path / "meetings"
    d.mkdir()
    return d


def _create_meeting(meetings_dir, meeting_id, status, error=None):
    meeting_dir = meetings_dir / meeting_id
    meeting_dir.mkdir()
    metadata = {"id": meeting_id, "status": status}
    if error is not None:
        metadata["error"] = error
    (meeting_dir / "metadata.json").write_text(json.dumps(metadata))
    return meeting_dir


class TestRecoverStuckMeetings:
    def test_recovers_processing_meetings(self, meetings_dir):
        _create_meeting(meetings_dir, "m1", "processing")
        _create_meeting(meetings_dir, "m2", "processing")

        with patch("backend.services.recovery.MEETINGS_DIR", meetings_dir):
            recovered = recover_stuck_meetings()

        assert sorted(recovered) == ["m1", "m2"]

        for mid in ["m1", "m2"]:
            metadata = json.loads(
                (meetings_dir / mid / "metadata.json").read_text()
            )
            assert metadata["status"] == "error"
            assert metadata["error"] == "Transcription interrupted by app restart"

    def test_ignores_non_processing_meetings(self, meetings_dir):
        _create_meeting(meetings_dir, "ready1", "ready")
        _create_meeting(meetings_dir, "error1", "error", error="some error")

        with patch("backend.services.recovery.MEETINGS_DIR", meetings_dir):
            recovered = recover_stuck_meetings()

        assert recovered == []

        # Verify they were not modified
        ready_meta = json.loads(
            (meetings_dir / "ready1" / "metadata.json").read_text()
        )
        assert ready_meta["status"] == "ready"

    def test_mixed_statuses(self, meetings_dir):
        _create_meeting(meetings_dir, "proc1", "processing")
        _create_meeting(meetings_dir, "ready1", "ready")
        _create_meeting(meetings_dir, "err1", "error")

        with patch("backend.services.recovery.MEETINGS_DIR", meetings_dir):
            recovered = recover_stuck_meetings()

        assert sorted(recovered) == ["proc1"]

    def test_empty_meetings_dir(self, meetings_dir):
        with patch("backend.services.recovery.MEETINGS_DIR", meetings_dir):
            recovered = recover_stuck_meetings()

        assert recovered == []

    def test_skips_malformed_metadata(self, meetings_dir):
        bad_dir = meetings_dir / "bad"
        bad_dir.mkdir()
        (bad_dir / "metadata.json").write_text("not json")

        _create_meeting(meetings_dir, "good", "processing")

        with patch("backend.services.recovery.MEETINGS_DIR", meetings_dir):
            recovered = recover_stuck_meetings()

        assert recovered == ["good"]

    def test_logs_recovered_meetings(self, meetings_dir, caplog):
        _create_meeting(meetings_dir, "m1", "processing")

        with patch("backend.services.recovery.MEETINGS_DIR", meetings_dir):
            import logging

            with caplog.at_level(logging.INFO):
                recover_stuck_meetings()

        assert "Recovered stuck meeting: m1" in caplog.text
        assert "Recovered 1 stuck meeting(s)" in caplog.text
