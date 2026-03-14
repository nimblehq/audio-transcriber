from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.schemas import JobStatus, MeetingStatus
from backend.services.job_queue import job_queue


class TestUploadFlow:
    """Upload a file and verify all artifacts are created on disk."""

    @patch("backend.routers.meetings.start_transcription")
    async def test_upload_creates_meeting_with_job(self, mock_start, client, sample_audio: Path, meetings_dir: Path):
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("recording.wav", f, "audio/wav")},
                data={"title": "Sprint Review", "meeting_type": "interview"},
            )

        assert res.status_code == 200
        data = res.json()
        meeting_id = data["meeting_id"]
        job_id = data["job_id"]

        # Verify meeting directory and files exist on disk
        meeting_dir = meetings_dir / meeting_id
        assert meeting_dir.exists()
        assert (meeting_dir / "metadata.json").exists()
        assert (meeting_dir / "audio.wav").exists()

        # Verify metadata content
        meta = json.loads((meeting_dir / "metadata.json").read_text())
        assert meta["title"] == "Sprint Review"
        assert meta["type"] == "interview"
        assert meta["status"] == "processing"
        assert meta["audio_filename"] == "audio.wav"
        assert meta["job_id"] == job_id

        # Verify job was created in the queue
        job = job_queue.get_job(job_id)
        assert job is not None
        assert job.meeting_id == meeting_id

        # Verify transcription was started
        mock_start.assert_called_once_with(meeting_id, job_id)


class TestTranscriptionCompletionFlow:
    """Upload → simulate transcription completing → verify transcript is retrievable."""

    @patch("backend.routers.meetings.start_transcription")
    async def test_full_transcription_lifecycle(self, mock_start, client, sample_audio: Path, meetings_dir: Path):
        # Step 1: Upload
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("call.wav", f, "audio/wav")},
                data={"title": "Client Call", "meeting_type": "sales"},
            )

        meeting_id = res.json()["meeting_id"]
        job_id = res.json()["job_id"]
        meeting_dir = meetings_dir / meeting_id

        # Verify initial state is PROCESSING
        detail = await client.get(f"/api/meetings/{meeting_id}")
        assert detail.json()["metadata"]["status"] == "processing"
        assert detail.json()["transcript"] is None

        # Step 2: Simulate transcription completion (what transcriber.py does)
        transcript_data = {
            "segments": [
                {"id": "seg_0000", "start": 0.0, "end": 3.5, "speaker": "SPEAKER_00", "text": "Hello, thanks for joining."},
                {"id": "seg_0001", "start": 4.0, "end": 8.2, "speaker": "SPEAKER_01", "text": "Happy to be here."},
                {"id": "seg_0002", "start": 8.5, "end": 15.0, "speaker": "SPEAKER_00", "text": "Let's discuss the proposal."},
            ],
            "language": "en",
        }
        (meeting_dir / "transcript.json").write_text(json.dumps(transcript_data))

        meta = json.loads((meeting_dir / "metadata.json").read_text())
        meta["status"] = "ready"
        meta["duration_seconds"] = 15.0
        meta["speakers"] = {"SPEAKER_00": "SPEAKER_00", "SPEAKER_01": "SPEAKER_01"}
        (meeting_dir / "metadata.json").write_text(json.dumps(meta))

        job_queue.update_job(job_id, status=JobStatus.COMPLETED, progress=100, stage="done")

        # Step 3: Verify meeting is now READY with transcript
        detail = await client.get(f"/api/meetings/{meeting_id}")
        assert detail.status_code == 200
        data = detail.json()
        assert data["metadata"]["status"] == "ready"
        assert data["metadata"]["duration_seconds"] == 15.0
        assert data["transcript"] is not None
        assert len(data["transcript"]["segments"]) == 3
        assert data["transcript"]["segments"][0]["text"] == "Hello, thanks for joining."

        # Verify job shows as completed
        job = job_queue.get_job(job_id)
        assert job.status == JobStatus.COMPLETED

        # Step 4: Verify it appears in the meeting list
        list_res = await client.get("/api/meetings")
        meetings = list_res.json()
        assert any(m["id"] == meeting_id and m["status"] == "ready" for m in meetings)


class TestRetryFlow:
    """Failed transcription → retry → verify new job is created."""

    @patch("backend.routers.meetings.start_transcription")
    async def test_retry_failed_transcription(self, mock_start, client, meetings_dir: Path, sample_audio: Path, sample_metadata_error: dict):
        # Step 1: Set up a failed meeting on disk
        meeting_id = sample_metadata_error["id"]
        meeting_dir = meetings_dir / meeting_id
        meeting_dir.mkdir()
        (meeting_dir / "metadata.json").write_text(json.dumps(sample_metadata_error))
        shutil.copy(sample_audio, meeting_dir / sample_metadata_error["audio_filename"])

        # Verify it shows as error
        detail = await client.get(f"/api/meetings/{meeting_id}")
        assert detail.json()["metadata"]["status"] == "error"

        # Step 2: Retry
        res = await client.post(f"/api/meetings/{meeting_id}/retry")
        assert res.status_code == 200
        new_job_id = res.json()["job_id"]

        # Step 3: Verify status changed to processing with a new job
        detail = await client.get(f"/api/meetings/{meeting_id}")
        meta = detail.json()["metadata"]
        assert meta["status"] == "processing"
        assert meta["job_id"] == new_job_id

        # Verify new job exists in the queue
        job = job_queue.get_job(new_job_id)
        assert job is not None
        assert job.meeting_id == meeting_id

        mock_start.assert_called_once_with(meeting_id, new_job_id)


class TestDeleteFlow:
    """Upload → delete → verify all files removed."""

    @patch("backend.routers.meetings.start_transcription")
    async def test_upload_then_delete(self, mock_start, client, sample_audio: Path, meetings_dir: Path):
        # Step 1: Upload a meeting
        with open(sample_audio, "rb") as f:
            res = await client.post(
                "/api/meetings",
                files={"file": ("meeting.wav", f, "audio/wav")},
                data={"title": "To Be Deleted"},
            )

        meeting_id = res.json()["meeting_id"]
        meeting_dir = meetings_dir / meeting_id
        assert meeting_dir.exists()

        # Step 2: Verify it appears in the list
        list_res = await client.get("/api/meetings")
        assert any(m["id"] == meeting_id for m in list_res.json())

        # Step 3: Delete
        del_res = await client.delete(f"/api/meetings/{meeting_id}")
        assert del_res.status_code == 200
        assert del_res.json()["ok"] is True

        # Step 4: Verify directory is gone
        assert not meeting_dir.exists()

        # Step 5: Verify it no longer appears in the list
        list_res = await client.get("/api/meetings")
        assert not any(m["id"] == meeting_id for m in list_res.json())

        # Step 6: Verify GET returns 404
        detail = await client.get(f"/api/meetings/{meeting_id}")
        assert detail.status_code == 404
