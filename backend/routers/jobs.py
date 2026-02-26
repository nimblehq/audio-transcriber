from fastapi import APIRouter, HTTPException

from backend.schemas import JobInfo
from backend.services.job_queue import job_queue

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobInfo)
async def get_job(job_id: str):
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
