from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response

from backend.schemas import (
    MeetingDetail,
    MeetingMetadata,
    MeetingStatus,
    MeetingSummary,
    MeetingType,
    MeetingUpdate,
    Transcript,
)
from backend.services.job_queue import job_queue
from backend.services.transcriber import start_transcription
from config import MAX_UPLOAD_SIZE, MEETINGS_DIR

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".webm"}


def _load_metadata(meeting_id: str) -> MeetingMetadata:
    meta_path = MEETINGS_DIR / meeting_id / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Meeting not found")
    with open(meta_path) as f:
        return MeetingMetadata(**json.load(f))


def _save_metadata(metadata: MeetingMetadata):
    meta_path = MEETINGS_DIR / metadata.id / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(mode="json"), f, ensure_ascii=False, indent=2, default=str)


@router.get("/meetings", response_model=list[MeetingSummary])
async def list_meetings():
    meetings = []
    if not MEETINGS_DIR.exists():
        return meetings

    for meeting_dir in MEETINGS_DIR.iterdir():
        if not meeting_dir.is_dir():
            continue
        meta_path = meeting_dir / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            with open(meta_path) as f:
                meta = MeetingMetadata(**json.load(f))
            meetings.append(MeetingSummary(
                id=meta.id,
                title=meta.title,
                type=meta.type,
                created_at=meta.created_at,
                duration_seconds=meta.duration_seconds,
                status=meta.status,
            ))
        except Exception:
            continue

    meetings.sort(key=lambda m: m.created_at, reverse=True)
    return meetings


@router.post("/meetings")
async def create_meeting(
    file: UploadFile = File(...),
    title: str = Form(""),
    meeting_type: str = Form("other"),
    language: str = Form("auto"),
    num_speakers: str = Form("auto"),
):
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 500MB)")

    meeting_id = str(uuid.uuid4())
    meeting_dir = MEETINGS_DIR / meeting_id
    meeting_dir.mkdir(parents=True)

    # Save audio file with original extension
    audio_filename = f"audio{ext}"
    audio_path = meeting_dir / audio_filename
    audio_path.write_bytes(content)

    # Create job
    job = job_queue.create_job(meeting_id)

    # Create metadata
    effective_title = title.strip() or Path(file.filename).stem
    try:
        mt = MeetingType(meeting_type)
    except ValueError:
        mt = MeetingType.OTHER

    effective_language = language.strip() if language.strip() != "auto" else "auto"
    effective_num_speakers = None
    if num_speakers.strip() != "auto":
        try:
            effective_num_speakers = int(num_speakers)
        except ValueError:
            pass

    metadata = MeetingMetadata(
        id=meeting_id,
        title=effective_title,
        type=mt,
        audio_filename=audio_filename,
        language=effective_language,
        num_speakers=effective_num_speakers,
        status=MeetingStatus.PROCESSING,
        job_id=job.id,
    )
    _save_metadata(metadata)

    # Start transcription
    start_transcription(meeting_id, job.id)

    return {"meeting_id": meeting_id, "job_id": job.id}


@router.post("/meetings/{meeting_id}/retry")
async def retry_transcription(meeting_id: str):
    metadata = _load_metadata(meeting_id)

    job = job_queue.create_job(meeting_id)
    metadata.status = MeetingStatus.PROCESSING
    metadata.job_id = job.id
    _save_metadata(metadata)

    start_transcription(meeting_id, job.id)

    return {"meeting_id": meeting_id, "job_id": job.id}


@router.get("/meetings/{meeting_id}", response_model=MeetingDetail)
async def get_meeting(meeting_id: str):
    metadata = _load_metadata(meeting_id)

    transcript = None
    transcript_path = MEETINGS_DIR / meeting_id / "transcript.json"
    if transcript_path.exists():
        with open(transcript_path) as f:
            transcript = Transcript(**json.load(f))

    return MeetingDetail(metadata=metadata, transcript=transcript)


@router.patch("/meetings/{meeting_id}", response_model=MeetingMetadata)
async def update_meeting(meeting_id: str, update: MeetingUpdate):
    metadata = _load_metadata(meeting_id)

    if update.title is not None:
        metadata.title = update.title
    if update.type is not None:
        metadata.type = update.type
    if update.speakers is not None:
        metadata.speakers = update.speakers

    _save_metadata(metadata)
    return metadata


@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    meeting_dir = MEETINGS_DIR / meeting_id
    if not meeting_dir.exists():
        raise HTTPException(status_code=404, detail="Meeting not found")
    shutil.rmtree(meeting_dir)
    return {"ok": True}


@router.get("/meetings/{meeting_id}/audio")
async def stream_audio(meeting_id: str):
    metadata = _load_metadata(meeting_id)
    audio_path = MEETINGS_DIR / meeting_id / metadata.audio_filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    ext = audio_path.suffix.lower()
    media_types = {
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
        ".m4a": "audio/mp4",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(str(audio_path), media_type=media_type)
