from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.services.job_queue import job_queue


@pytest.fixture
def processing_meeting(meetings_dir: Path, sample_metadata_processing: dict, sample_audio: Path) -> str:
    """Create a PROCESSING meeting on disk with a real job. Returns the meeting ID."""
    meeting_id = sample_metadata_processing["id"]
    meeting_dir = meetings_dir / meeting_id
    meeting_dir.mkdir()

    job = job_queue.create_job(meeting_id)
    sample_metadata_processing["job_id"] = job.id
    (meeting_dir / "metadata.json").write_text(json.dumps(sample_metadata_processing))
    shutil.copy(sample_audio, meeting_dir / sample_metadata_processing["audio_filename"])

    return meeting_id


@pytest.fixture
def error_meeting(meetings_dir: Path, sample_metadata_error: dict, sample_audio: Path) -> str:
    """Create an ERROR meeting on disk. Returns the meeting ID."""
    meeting_id = sample_metadata_error["id"]
    meeting_dir = meetings_dir / meeting_id
    meeting_dir.mkdir()

    (meeting_dir / "metadata.json").write_text(json.dumps(sample_metadata_error))
    shutil.copy(sample_audio, meeting_dir / sample_metadata_error["audio_filename"])

    return meeting_id


class TestListMeetings:
    async def test_empty_state(self, client):
        res = await client.get("/api/meetings")
        assert res.status_code == 200
        assert res.json() == []

    async def test_returns_meetings(self, client, populated_meeting):
        res = await client.get("/api/meetings")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["id"] == populated_meeting
        assert data[0]["title"] == "Weekly Standup"

    async def test_sort_order_newest_first(self, client, meetings_dir: Path, sample_audio: Path):
        """Multiple meetings are returned sorted by created_at descending."""
        for i, date in enumerate(["2026-01-10T10:00:00", "2026-01-20T10:00:00", "2026-01-15T10:00:00"]):
            mid = f"meeting-{i}"
            d = meetings_dir / mid
            d.mkdir()
            meta = {
                "id": mid,
                "title": f"Meeting {i}",
                "type": "other",
                "created_at": date,
                "audio_filename": "sample.wav",
                "status": "ready",
                "speakers": {},
            }
            (d / "metadata.json").write_text(json.dumps(meta))

        res = await client.get("/api/meetings")
        data = res.json()
        assert len(data) == 3
        assert data[0]["id"] == "meeting-1"  # Jan 20
        assert data[1]["id"] == "meeting-2"  # Jan 15
        assert data[2]["id"] == "meeting-0"  # Jan 10


class TestCreateMeeting:
    @patch("backend.routers.meetings.start_transcription")
    async def test_upload_valid_file(self, mock_start, client, sample_audio: Path):
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("test.wav", f, "audio/wav")},
                data={"title": "Test Meeting", "meeting_type": "interview"},
            )
        assert res.status_code == 200
        data = res.json()
        assert "meeting_id" in data
        assert "job_id" in data
        mock_start.assert_called_once()

    @patch("backend.routers.meetings.start_transcription")
    async def test_upload_uses_filename_as_default_title(self, mock_start, client, sample_audio: Path):
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("my-recording.wav", f, "audio/wav")},
                data={"title": "", "meeting_type": "other"},
            )
        assert res.status_code == 200
        meeting_id = res.json()["meeting_id"]

        detail = await client.get(f"/api/meetings/{meeting_id}")
        assert detail.json()["metadata"]["title"] == "my-recording"

    async def test_upload_invalid_extension(self, client, tmp_path: Path):
        fake = tmp_path / "test.txt"
        fake.write_text("not audio")
        with open(fake, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("test.txt", f, "text/plain")},
                data={"title": "Bad File"},
            )
        assert res.status_code == 400
        assert "Unsupported file format" in res.json()["detail"]

    @patch("backend.routers.meetings.start_transcription")
    async def test_upload_creates_files_on_disk(self, mock_start, client, sample_audio: Path, meetings_dir: Path):
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("test.wav", f, "audio/wav")},
                data={"title": "Disk Test"},
            )
        meeting_id = res.json()["meeting_id"]
        meeting_dir = meetings_dir / meeting_id
        assert meeting_dir.exists()
        assert (meeting_dir / "metadata.json").exists()
        assert (meeting_dir / "audio.wav").exists()

    @patch("backend.routers.meetings.start_transcription")
    async def test_preprocess_audio_defaults_to_true(self, mock_start, client, sample_audio: Path, meetings_dir: Path):
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("test.wav", f, "audio/wav")},
                data={"title": "Preprocess Test"},
            )
        meeting_id = res.json()["meeting_id"]
        meta = json.loads((meetings_dir / meeting_id / "metadata.json").read_text())
        assert meta["preprocess_audio"] is True

    @patch("backend.routers.meetings.start_transcription")
    async def test_preprocess_audio_can_be_disabled(self, mock_start, client, sample_audio: Path, meetings_dir: Path):
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("test.wav", f, "audio/wav")},
                data={"title": "No Preprocess", "preprocess_audio": "false"},
            )
        meeting_id = res.json()["meeting_id"]
        meta = json.loads((meetings_dir / meeting_id / "metadata.json").read_text())
        assert meta["preprocess_audio"] is False

    @patch("backend.routers.meetings.start_transcription")
    async def test_audio_analysis_defaults_to_disabled(
        self, mock_start, client, sample_audio: Path, meetings_dir: Path
    ):
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("test.wav", f, "audio/wav")},
                data={"title": "Default Audio Analysis"},
            )
        meeting_id = res.json()["meeting_id"]
        meta = json.loads((meetings_dir / meeting_id / "metadata.json").read_text())
        assert meta["audio_analysis_enabled"] is False
        assert meta["audio_analysis_status"] is None

    @patch("backend.routers.meetings.start_transcription")
    async def test_audio_analysis_can_be_enabled(self, mock_start, client, sample_audio: Path, meetings_dir: Path):
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("test.wav", f, "audio/wav")},
                data={"title": "Audio Analysis On", "audio_analysis_enabled": "true"},
            )
        meeting_id = res.json()["meeting_id"]
        meta = json.loads((meetings_dir / meeting_id / "metadata.json").read_text())
        assert meta["audio_analysis_enabled"] is True


class TestGetMeeting:
    async def test_existing_meeting(self, client, populated_meeting):
        res = await client.get(f"/api/meetings/{populated_meeting}")
        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["id"] == populated_meeting
        assert data["transcript"] is not None
        assert len(data["transcript"]["segments"]) == 4

    async def test_nonexistent_meeting(self, client):
        res = await client.get("/api/meetings/nonexistent")
        assert res.status_code == 404


class TestUpdateMeeting:
    async def test_update_title(self, client, populated_meeting):
        res = await client.patch(
            f"/api/meetings/{populated_meeting}",
            json={"title": "Updated Title"},
        )
        assert res.status_code == 200
        assert res.json()["title"] == "Updated Title"

    async def test_update_type(self, client, populated_meeting):
        res = await client.patch(
            f"/api/meetings/{populated_meeting}",
            json={"type": "sales"},
        )
        assert res.status_code == 200
        assert res.json()["type"] == "sales"

    async def test_update_speakers(self, client, populated_meeting):
        speakers = {"SPEAKER_00": "Charlie", "SPEAKER_01": "Dana"}
        res = await client.patch(
            f"/api/meetings/{populated_meeting}",
            json={"speakers": speakers},
        )
        assert res.status_code == 200
        assert res.json()["speakers"] == speakers

    async def test_update_nonexistent_meeting(self, client):
        res = await client.patch("/api/meetings/nonexistent", json={"title": "X"})
        assert res.status_code == 404


class TestUpdateSegmentSpeaker:
    async def test_rename_segment_speaker(self, client, populated_meeting):
        res = await client.patch(
            f"/api/meetings/{populated_meeting}/segments/speaker",
            json={"segment_id": "seg-001", "speaker_name": "Charlie"},
        )
        assert res.status_code == 200
        assert res.json()["ok"] is True

        # Verify the speaker mapping was saved
        detail = await client.get(f"/api/meetings/{populated_meeting}")
        speakers = detail.json()["metadata"]["speakers"]
        assert "Charlie" in speakers.values()

    async def test_missing_segment(self, client, populated_meeting):
        res = await client.patch(
            f"/api/meetings/{populated_meeting}/segments/speaker",
            json={"segment_id": "nonexistent", "speaker_name": "X"},
        )
        assert res.status_code == 404
        assert "Segment not found" in res.json()["detail"]

    async def test_missing_transcript(self, client, meetings_dir: Path):
        """Meeting exists but has no transcript.json."""
        mid = "no-transcript"
        d = meetings_dir / mid
        d.mkdir()
        meta = {
            "id": mid,
            "title": "No Transcript",
            "type": "other",
            "audio_filename": "audio.wav",
            "status": "processing",
            "speakers": {},
        }
        (d / "metadata.json").write_text(json.dumps(meta))

        res = await client.patch(
            f"/api/meetings/{mid}/segments/speaker",
            json={"segment_id": "seg-001", "speaker_name": "X"},
        )
        assert res.status_code == 404
        assert "Transcript not found" in res.json()["detail"]


class TestRetryTranscription:
    @patch("backend.routers.meetings.start_transcription")
    async def test_retry_creates_new_job(self, mock_start, client, error_meeting):
        res = await client.post(f"/api/meetings/{error_meeting}/retry")
        assert res.status_code == 200
        data = res.json()
        assert "job_id" in data
        mock_start.assert_called_once()

        # Verify status changed to processing
        detail = await client.get(f"/api/meetings/{error_meeting}")
        assert detail.json()["metadata"]["status"] == "processing"

    async def test_retry_nonexistent_meeting(self, client):
        res = await client.post("/api/meetings/nonexistent/retry")
        assert res.status_code == 404

    @patch("backend.routers.meetings.start_transcription")
    async def test_retry_preserves_audio_analysis_opt_in(
        self, mock_start, client, meetings_dir: Path, sample_metadata_error: dict, sample_audio: Path
    ):
        meeting_id = sample_metadata_error["id"]
        sample_metadata_error["audio_analysis_enabled"] = True
        sample_metadata_error["audio_analysis_status"] = "failed"
        meeting_dir = meetings_dir / meeting_id
        meeting_dir.mkdir()
        (meeting_dir / "metadata.json").write_text(json.dumps(sample_metadata_error))
        shutil.copy(sample_audio, meeting_dir / sample_metadata_error["audio_filename"])

        res = await client.post(f"/api/meetings/{meeting_id}/retry")
        assert res.status_code == 200

        meta = json.loads((meetings_dir / meeting_id / "metadata.json").read_text())
        assert meta["audio_analysis_enabled"] is True
        assert meta["audio_analysis_status"] is None


class TestDeleteMeeting:
    async def test_delete_meeting(self, client, populated_meeting, meetings_dir: Path):
        res = await client.delete(f"/api/meetings/{populated_meeting}")
        assert res.status_code == 200
        assert res.json()["ok"] is True
        assert not (meetings_dir / populated_meeting).exists()

    async def test_delete_nonexistent_meeting(self, client):
        res = await client.delete("/api/meetings/nonexistent")
        assert res.status_code == 404


class TestStreamAudio:
    async def test_stream_audio(self, client, populated_meeting):
        res = await client.get(f"/api/meetings/{populated_meeting}/audio")
        assert res.status_code == 200
        assert res.headers["content-type"] == "audio/wav"

    async def test_audio_missing_file(self, client, populated_meeting, meetings_dir: Path):
        """Metadata exists but audio file was deleted."""
        audio = meetings_dir / populated_meeting / "sample.wav"
        audio.unlink()

        res = await client.get(f"/api/meetings/{populated_meeting}/audio")
        assert res.status_code == 404

    async def test_audio_nonexistent_meeting(self, client):
        res = await client.get("/api/meetings/nonexistent/audio")
        assert res.status_code == 404
