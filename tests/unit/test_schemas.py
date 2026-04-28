from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.schemas import (
    AudioAnalysis,
    AudioAnalysisStatus,
    EmotionAnnotation,
    EmotionCategory,
    JobInfo,
    JobStage,
    JobStatus,
    MeetingDetail,
    MeetingMetadata,
    MeetingStatus,
    MeetingSummary,
    MeetingType,
    MeetingUpdate,
    ProsodyAnnotation,
    ProsodyUnavailable,
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
        assert m.error is None
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

    def test_error_field(self):
        m = MeetingMetadata(id="m1", title="Test", error="Transcription cancelled by user")
        assert m.error == "Transcription cancelled by user"

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


class TestAudioAnalysisFields:
    def test_metadata_default_audio_analysis_disabled(self):
        m = MeetingMetadata(id="m1", title="Test")
        assert m.audio_analysis_enabled is False
        assert m.audio_analysis_status is None

    def test_metadata_with_audio_analysis(self):
        m = MeetingMetadata(
            id="m1",
            title="Test",
            audio_analysis_enabled=True,
            audio_analysis_status=AudioAnalysisStatus.COMPLETED,
        )
        assert m.audio_analysis_enabled is True
        assert m.audio_analysis_status == AudioAnalysisStatus.COMPLETED

    def test_audio_analysis_status_values(self):
        assert AudioAnalysisStatus.COMPLETED == "completed"
        assert AudioAnalysisStatus.FAILED == "failed"
        assert AudioAnalysisStatus.UNAVAILABLE == "unavailable"

    def test_emotion_category_values(self):
        assert EmotionCategory.NEUTRAL == "neutral"
        assert EmotionCategory.CONFIDENT == "confident"
        assert EmotionCategory.FRUSTRATED == "frustrated"
        assert EmotionCategory.UNCERTAIN == "uncertain"
        assert EmotionCategory.ENGAGED == "engaged"
        assert EmotionCategory.DISENGAGED == "disengaged"

    def test_emotion_annotation_creation(self):
        a = EmotionAnnotation(
            segment_id="seg-1",
            speaker="SPEAKER_00",
            start=0.0,
            end=2.5,
            primary_emotion=EmotionCategory.ENGAGED,
            confidence=0.78,
            emotion_scores={"engaged": 0.78, "neutral": 0.22},
            low_confidence=False,
        )
        assert a.primary_emotion == EmotionCategory.ENGAGED
        assert a.low_confidence is False

    def test_audio_analysis_default_emotions_empty(self):
        a = AudioAnalysis(status=AudioAnalysisStatus.UNAVAILABLE, reason="language_not_supported:fr")
        assert a.emotions == []
        assert a.reason == "language_not_supported:fr"

    def test_job_stage_emotion_analysis(self):
        assert JobStage.EMOTION_ANALYSIS == "emotion_analysis"

    def test_job_stage_prosody_extraction(self):
        assert JobStage.PROSODY_EXTRACTION == "prosody_extraction"


class TestProsodyAnnotation:
    def test_creation(self):
        p = ProsodyAnnotation(
            segment_id="seg-1",
            speaker="SPEAKER_00",
            start=0.0,
            end=2.5,
            volume_mean=0.6,
            volume_variance=0.02,
            pitch_mean=180.5,
            pitch_variance=320.4,
            speaking_rate=145.0,
            pause_ratio=0.12,
        )
        assert p.segment_id == "seg-1"
        assert p.volume_mean == 0.6
        assert p.pitch_mean == 180.5
        assert p.speaking_rate == 145.0

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            ProsodyAnnotation(
                segment_id="seg-1",
                speaker="SPEAKER_00",
                start=0.0,
                end=2.5,
                volume_mean=0.6,
                volume_variance=0.02,
                pitch_mean=180.5,
                pitch_variance=320.4,
                speaking_rate=145.0,
            )


class TestProsodyUnavailable:
    def test_creation(self):
        u = ProsodyUnavailable(segment_id="seg-1", reason="non_speech")
        assert u.segment_id == "seg-1"
        assert u.reason == "non_speech"


class TestAudioAnalysisProsodyFields:
    def test_audio_analysis_default_prosody_empty(self):
        a = AudioAnalysis(status=AudioAnalysisStatus.UNAVAILABLE)
        assert a.prosody == []
        assert a.prosody_unavailable == []
        assert a.prosody_status is None
        assert a.prosody_reason is None
        assert a.emotion_status is None
        assert a.emotion_reason is None

    def test_audio_analysis_with_prosody(self):
        prosody = [
            ProsodyAnnotation(
                segment_id="seg-1",
                speaker="SPEAKER_00",
                start=0.0,
                end=1.0,
                volume_mean=0.5,
                volume_variance=0.01,
                pitch_mean=150.0,
                pitch_variance=20.0,
                speaking_rate=120.0,
                pause_ratio=0.1,
            )
        ]
        a = AudioAnalysis(
            status=AudioAnalysisStatus.COMPLETED,
            prosody_status=AudioAnalysisStatus.COMPLETED,
            prosody=prosody,
            prosody_unavailable=[ProsodyUnavailable(segment_id="seg-2", reason="non_speech")],
        )
        assert len(a.prosody) == 1
        assert len(a.prosody_unavailable) == 1
        assert a.prosody_unavailable[0].reason == "non_speech"

    def test_audio_analysis_per_stage_status(self):
        a = AudioAnalysis(
            status=AudioAnalysisStatus.COMPLETED,
            emotion_status=AudioAnalysisStatus.UNAVAILABLE,
            emotion_reason="language_not_supported:fr",
            prosody_status=AudioAnalysisStatus.COMPLETED,
        )
        assert a.emotion_status == AudioAnalysisStatus.UNAVAILABLE
        assert a.prosody_status == AudioAnalysisStatus.COMPLETED
