from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.schemas import JobStatus
from backend.services.job_queue import JobQueue


class TestCreateJob:
    def test_returns_job_info_with_pending_status(self):
        queue = JobQueue()
        job = queue.create_job("meeting-1")

        assert job.meeting_id == "meeting-1"
        assert job.status == JobStatus.PENDING
        assert job.progress == 0
        assert job.stage == ""
        assert job.error is None

    def test_assigns_unique_ids(self):
        queue = JobQueue()
        job1 = queue.create_job("m1")
        job2 = queue.create_job("m2")

        assert job1.id != job2.id

    def test_sets_created_and_updated_timestamps(self):
        queue = JobQueue()
        job = queue.create_job("m1")

        assert job.created_at is not None
        assert job.updated_at is not None
        assert job.created_at == job.updated_at


class TestGetJob:
    def test_returns_created_job(self):
        queue = JobQueue()
        created = queue.create_job("m1")
        fetched = queue.get_job(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.meeting_id == "m1"

    def test_returns_none_for_unknown_id(self):
        queue = JobQueue()
        assert queue.get_job("nonexistent") is None


class TestUpdateJob:
    def test_updates_status(self):
        queue = JobQueue()
        job = queue.create_job("m1")
        queue.update_job(job.id, status=JobStatus.PROCESSING)

        assert queue.get_job(job.id).status == JobStatus.PROCESSING

    def test_updates_progress_and_stage(self):
        queue = JobQueue()
        job = queue.create_job("m1")
        queue.update_job(job.id, progress=50, stage="transcribing")

        updated = queue.get_job(job.id)
        assert updated.progress == 50
        assert updated.stage == "transcribing"

    def test_updates_error(self):
        queue = JobQueue()
        job = queue.create_job("m1")
        queue.update_job(job.id, error="something broke")

        assert queue.get_job(job.id).error == "something broke"

    def test_only_updates_specified_fields(self):
        queue = JobQueue()
        job = queue.create_job("m1")
        queue.update_job(job.id, status=JobStatus.PROCESSING)
        queue.update_job(job.id, progress=50)

        updated = queue.get_job(job.id)
        assert updated.status == JobStatus.PROCESSING
        assert updated.progress == 50

    def test_updates_timestamp(self):
        queue = JobQueue()
        job = queue.create_job("m1")
        original_updated_at = job.updated_at
        queue.update_job(job.id, progress=10)

        assert queue.get_job(job.id).updated_at >= original_updated_at

    def test_silently_ignores_missing_job(self):
        queue = JobQueue()
        queue.update_job("nonexistent", status=JobStatus.FAILED)  # no exception


class TestClear:
    def test_removes_all_jobs(self):
        queue = JobQueue()
        job1 = queue.create_job("m1")
        job2 = queue.create_job("m2")
        queue.clear()

        assert queue.get_job(job1.id) is None
        assert queue.get_job(job2.id) is None


class TestThreadSafety:
    def test_concurrent_create_and_update(self):
        queue = JobQueue()
        num_jobs = 50

        def create_and_update(i: int) -> str:
            job = queue.create_job(f"meeting-{i}")
            queue.update_job(job.id, status=JobStatus.PROCESSING, progress=i)
            return job.id

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_update, i) for i in range(num_jobs)]
            job_ids = [f.result() for f in as_completed(futures)]

        assert len(set(job_ids)) == num_jobs

        for job_id in job_ids:
            job = queue.get_job(job_id)
            assert job is not None
            assert job.status == JobStatus.PROCESSING
