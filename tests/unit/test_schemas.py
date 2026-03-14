from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.schemas import (
    JobInfo,
    JobStage,
    JobStatus,
    MeetingDetail,
    MeetingMetadata,
    MeetingStatus,
    MeetingSummary,
    MeetingType,
    MeetingUpdate,
    SegmentSpeakerUpdate,
    Transcript,
    TranscriptSegment,
)


class TestMeetingTypeEnum:
    def test_values(self):
        assert MeetingType.INTERVIEW == "interview"
        assert MeetingType.SALES == "sales"
        assert MeetingType.CLIENT == "client"
        assert MeetingType.OTHER == "other"

    def test_all_members(self):
        assert set(MeetingType) == {
            MeetingType.INTERVIEW,
            MeetingType.SALES,
            MeetingType.CLIENT,
            MeetingType.OTHER,
        }


class TestMeetingStatusEnum:
    def test_values(self):
        assert MeetingStatus.PROCESSING == "processing"
        assert MeetingStatus.READY == "ready"
        assert MeetingStatus.ERROR == "error"

    def test_all_members(self):
        assert len(MeetingStatus) == 3


class TestJobStatusEnum:
    def test_values(self):
        assert JobStatus.PENDING == "pending"
        assert JobStatus.PROCESSING == "processing"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"

    def test_all_members(self):
        assert len(JobStatus) == 4


class TestJobStageEnum:
    def test_values(self):
        assert JobStage.UPLOADING == "uploading"
        assert JobStage.TRANSCRIBING == "transcribing"
        assert JobStage.ALIGNING == "aligning"
        assert JobStage.DIARIZING == "diarizing"


class TestTranscriptSegment:
    def test_creation(self):
        seg = TranscriptSegment(id="seg-1", start=0.0, end=5.5, speaker="SPEAKER_00", text="Hello")
        assert seg.id == "seg-1"
        assert seg.start == 0.0
        assert seg.end == 5.5
        assert seg.speaker == "SPEAKER_00"
        assert seg.text == "Hello"

    def test_serialization(self):
        seg = TranscriptSegment(id="seg-1", start=1.0, end=2.0, speaker="SPEAKER_01", text="Hi")
        data = seg.model_dump()
        assert data == {
            "id": "seg-1",
            "start": 1.0,
            "end": 2.0,
            "speaker": "SPEAKER_01",
            "text": "Hi",
        }

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            TranscriptSegment(id="seg-1", start=0.0, end=1.0, speaker="SPEAKER_00")


class TestTranscript:
    def test_defaults(self):
        t = Transcript(segments=[])
        assert t.segments == []
        assert t.language == "en"

    def test_with_segments(self):
        seg = TranscriptSegment(id="s1", start=0.0, end=1.0, speaker="SP00", text="Test")
        t = Transcript(segments=[seg], language="fr")
        assert len(t.segments) == 1
        assert t.language == "fr"


class TestMeetingMetadata:
    def test_defaults(self):
        m = MeetingMetadata(id="m1", title="Test")
        assert m.type == MeetingType.OTHER
        assert m.status == MeetingStatus.PROCESSING
        assert m.language == "auto"
        assert m.audio_filename == ""
        assert m.duration_seconds is None
        assert m.num_speakers is None
        assert m.job_id is None
        assert m.speakers == {}
        assert isinstance(m.created_at, datetime)

    def test_full_creation(self):
        m = MeetingMetadata(
            id="m1",
            title="Standup",
            type=MeetingType.INTERVIEW,
            status=MeetingStatus.READY,
            duration_seconds=120.0,
            audio_filename="audio.wav",
            num_speakers=3,
            job_id="j1",
            speakers={"SPEAKER_00": "Alice"},
        )
        assert m.type == MeetingType.INTERVIEW
        assert m.status == MeetingStatus.READY
        assert m.duration_seconds == 120.0

    def test_serialization_roundtrip(self):
        m = MeetingMetadata(id="m1", title="Test")
        data = m.model_dump()
        m2 = MeetingMetadata(**data)
        assert m2.id == m.id
        assert m2.title == m.title

    def test_from_fixture(self, sample_metadata: dict):
        m = MeetingMetadata(**sample_metadata)
        assert m.id == "test-meeting-001"
        assert m.status == MeetingStatus.READY
        assert m.speakers == {"SPEAKER_00": "Alice", "SPEAKER_01": "Bob"}


class TestMeetingUpdate:
    def test_all_none_by_default(self):
        u = MeetingUpdate()
        assert u.title is None
        assert u.type is None
        assert u.speakers is None

    def test_partial_update(self):
        u = MeetingUpdate(title="New Title")
        assert u.title == "New Title"
        assert u.type is None


class TestMeetingSummary:
    def test_creation(self):
        s = MeetingSummary(
            id="m1",
            title="Test",
            type=MeetingType.OTHER,
            created_at=datetime(2026, 1, 1),
            duration_seconds=60.0,
            status=MeetingStatus.READY,
        )
        assert s.duration_seconds == 60.0

    def test_nullable_duration(self):
        s = MeetingSummary(
            id="m1",
            title="Test",
            type=MeetingType.OTHER,
            created_at=datetime(2026, 1, 1),
            duration_seconds=None,
            status=MeetingStatus.PROCESSING,
        )
        assert s.duration_seconds is None


class TestMeetingDetail:
    def test_without_transcript(self):
        meta = MeetingMetadata(id="m1", title="Test")
        d = MeetingDetail(metadata=meta)
        assert d.transcript is None

    def test_with_transcript(self):
        meta = MeetingMetadata(id="m1", title="Test")
        t = Transcript(segments=[])
        d = MeetingDetail(metadata=meta, transcript=t)
        assert d.transcript is not None
        assert d.transcript.segments == []


class TestJobInfo:
    def test_creation(self):
        now = datetime(2026, 1, 1)
        j = JobInfo(
            id="j1",
            meeting_id="m1",
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        assert j.progress == 0
        assert j.stage == ""
        assert j.error is None

    def test_failed_job(self):
        now = datetime(2026, 1, 1)
        j = JobInfo(
            id="j1",
            meeting_id="m1",
            status=JobStatus.FAILED,
            error="Out of memory",
            created_at=now,
            updated_at=now,
        )
        assert j.error == "Out of memory"


class TestSegmentSpeakerUpdate:
    def test_creation(self):
        u = SegmentSpeakerUpdate(segment_id="seg-1", speaker_name="Alice")
        assert u.segment_id == "seg-1"
        assert u.speaker_name == "Alice"
