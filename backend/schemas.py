from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MeetingType(str, Enum):
    INTERVIEW = "interview"
    SALES = "sales"
    CLIENT = "client"
    OTHER = "other"


class MeetingStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStage(str, Enum):
    UPLOADING = "uploading"
    TRANSCRIBING = "transcribing"
    ALIGNING = "aligning"
    DIARIZING = "diarizing"


class TranscriptSegment(BaseModel):
    id: str
    start: float
    end: float
    speaker: str
    text: str


class Transcript(BaseModel):
    segments: list[TranscriptSegment]
    language: str = "en"


class MeetingMetadata(BaseModel):
    id: str
    title: str
    type: MeetingType = MeetingType.OTHER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: float | None = None
    audio_filename: str = ""
    status: MeetingStatus = MeetingStatus.PROCESSING
    language: str = "auto"
    num_speakers: int | None = None
    job_id: str | None = None
    speakers: dict[str, str] = Field(default_factory=dict)


class MeetingUpdate(BaseModel):
    title: str | None = None
    type: MeetingType | None = None
    speakers: dict[str, str] | None = None


class MeetingSummary(BaseModel):
    id: str
    title: str
    type: MeetingType
    created_at: datetime
    duration_seconds: float | None
    status: MeetingStatus


class MeetingDetail(BaseModel):
    metadata: MeetingMetadata
    transcript: Transcript | None = None


class JobInfo(BaseModel):
    id: str
    meeting_id: str
    status: JobStatus
    progress: int = 0
    stage: str = ""
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class AnalysisRequest(BaseModel):
    meeting_type: MeetingType | None = None
