from __future__ import annotations

import uuid
from datetime import datetime
from threading import Lock

from backend.schemas import JobInfo, JobStatus


class JobQueue:
    def __init__(self):
        self._jobs: dict[str, JobInfo] = {}
        self._lock = Lock()

    def create_job(self, meeting_id: str) -> JobInfo:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        job = JobInfo(
            id=job_id,
            meeting_id=meeting_id,
            status=JobStatus.PENDING,
            progress=0,
            stage="",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> JobInfo | None:
        with self._lock:
            return self._jobs.get(job_id)

    def clear(self):
        """Remove all jobs. Used for test cleanup."""
        with self._lock:
            self._jobs.clear()

    def update_job(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        progress: int | None = None,
        stage: str | None = None,
        error: str | None = None,
    ):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = progress
            if stage is not None:
                job.stage = stage
            if error is not None:
                job.error = error
            job.updated_at = datetime.utcnow()


job_queue = JobQueue()
