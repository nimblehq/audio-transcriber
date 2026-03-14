from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from backend.services.job_queue import job_queue


@pytest.fixture
def processing_meeting(meetings_dir: Path, sample_metadata_processing: dict, sample_audio: Path) -> str:
    """Create a PROCESSING meeting on disk. Returns the meeting ID."""
    meeting_id = sample_metadata_processing["id"]
    meeting_dir = meetings_dir / meeting_id
    meeting_dir.mkdir()

    (meeting_dir / "metadata.json").write_text(json.dumps(sample_metadata_processing))
    shutil.copy(sample_audio, meeting_dir / sample_metadata_processing["audio_filename"])

    # Create a matching job in the queue
    job = job_queue.create_job(meeting_id)
    # Update fixture to use the real job ID
    sample_metadata_processing["job_id"] = job.id
    (meeting_dir / "metadata.json").write_text(json.dumps(sample_metadata_processing))

    return meeting_id


@pytest.fixture
def ready_meeting(meetings_dir: Path, sample_metadata: dict, sample_audio: Path) -> str:
    """Create a READY meeting on disk. Returns the meeting ID."""
    meeting_id = sample_metadata["id"]
    meeting_dir = meetings_dir / meeting_id
    meeting_dir.mkdir()

    (meeting_dir / "metadata.json").write_text(json.dumps(sample_metadata))
    shutil.copy(sample_audio, meeting_dir / sample_metadata["audio_filename"])

    return meeting_id


class TestCancelEndpoint:
    async def test_cancel_processing_meeting(self, client, processing_meeting):
        res = await client.post(f"/api/meetings/{processing_meeting}/cancel")
        assert res.status_code == 200

        data = res.json()
        assert data["ok"] is True

        # Verify meeting status changed to error
        meeting_res = await client.get(f"/api/meetings/{processing_meeting}")
        meta = meeting_res.json()["metadata"]
        assert meta["status"] == "error"
        assert meta["error"] == "Transcription cancelled by user"

    async def test_cancel_sets_job_to_failed(self, client, processing_meeting, meetings_dir):
        # Get the job_id from metadata
        meta_path = meetings_dir / processing_meeting / "metadata.json"
        meta = json.loads(meta_path.read_text())
        job_id = meta["job_id"]

        await client.post(f"/api/meetings/{processing_meeting}/cancel")

        job = job_queue.get_job(job_id)
        assert job is not None
        assert job.status.value == "failed"
        assert job.error == "Transcription cancelled by user"

    async def test_cancel_non_processing_meeting_returns_409(self, client, ready_meeting):
        res = await client.post(f"/api/meetings/{ready_meeting}/cancel")
        assert res.status_code == 409

    async def test_cancel_nonexistent_meeting_returns_404(self, client):
        res = await client.post("/api/meetings/nonexistent/cancel")
        assert res.status_code == 404

    async def test_retry_after_cancel(self, client, processing_meeting):
        # Cancel first
        await client.post(f"/api/meetings/{processing_meeting}/cancel")

        # Verify retry works
        res = await client.post(f"/api/meetings/{processing_meeting}/retry")
        assert res.status_code == 200

        # Verify status is back to processing
        meeting_res = await client.get(f"/api/meetings/{processing_meeting}")
        meta = meeting_res.json()["metadata"]
        assert meta["status"] == "processing"
