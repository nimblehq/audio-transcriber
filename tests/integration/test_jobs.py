from __future__ import annotations

from backend.schemas import JobStatus
from backend.services.job_queue import job_queue


class TestGetJob:
    async def test_pending_job(self, client):
        job = job_queue.create_job("some-meeting")
        res = await client.get(f"/api/jobs/{job.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "pending"
        assert data["meeting_id"] == "some-meeting"

    async def test_completed_job(self, client):
        job = job_queue.create_job("some-meeting")
        job_queue.update_job(job.id, status=JobStatus.COMPLETED, progress=100)
        res = await client.get(f"/api/jobs/{job.id}")
        assert res.status_code == 200
        assert res.json()["status"] == "completed"
        assert res.json()["progress"] == 100

    async def test_failed_job(self, client):
        job = job_queue.create_job("some-meeting")
        job_queue.update_job(job.id, status=JobStatus.FAILED, error="Something broke")
        res = await client.get(f"/api/jobs/{job.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "failed"
        assert data["error"] == "Something broke"

    async def test_nonexistent_job(self, client):
        res = await client.get("/api/jobs/nonexistent")
        assert res.status_code == 404
