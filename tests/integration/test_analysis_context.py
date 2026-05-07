from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def base_metadata() -> dict:
    return json.loads((FIXTURES_DIR / "metadata.json").read_text())


@pytest.fixture
def base_transcript() -> dict:
    return json.loads((FIXTURES_DIR / "transcript.json").read_text())


def _write_meeting(
    meetings_dir: Path,
    sample_audio: Path,
    metadata: dict,
    transcript: dict | None = None,
    audio_analysis: dict | None = None,
) -> str:
    meeting_id = metadata["id"]
    meeting_dir = meetings_dir / meeting_id
    meeting_dir.mkdir()
    (meeting_dir / "metadata.json").write_text(json.dumps(metadata))
    if transcript is not None:
        (meeting_dir / "transcript.json").write_text(json.dumps(transcript))
    if audio_analysis is not None:
        (meeting_dir / "audio_analysis.json").write_text(json.dumps(audio_analysis))
    shutil.copy(sample_audio, meeting_dir / metadata["audio_filename"])
    return meeting_id


class TestGetAnalysisContext:
    async def test_returns_404_when_meeting_not_found(self, client):
        res = await client.get("/api/meetings/missing/analysis-context")
        assert res.status_code == 404

    async def test_opted_out_meeting_returns_empty_context(
        self,
        client,
        meetings_dir: Path,
        sample_audio: Path,
        base_metadata: dict,
        base_transcript: dict,
    ):
        # audio_analysis_enabled defaults to False — BR-4.4 backward compat.
        base_metadata["audio_analysis_enabled"] = False
        meeting_id = _write_meeting(meetings_dir, sample_audio, base_metadata, base_transcript)

        res = await client.get(f"/api/meetings/{meeting_id}/analysis-context")
        assert res.status_code == 200
        assert res.json() == {"context": ""}

    async def test_opted_in_with_no_audio_analysis_file_returns_unavailability_note(
        self,
        client,
        meetings_dir: Path,
        sample_audio: Path,
        base_metadata: dict,
        base_transcript: dict,
    ):
        base_metadata["audio_analysis_enabled"] = True
        meeting_id = _write_meeting(meetings_dir, sample_audio, base_metadata, base_transcript)

        res = await client.get(f"/api/meetings/{meeting_id}/analysis-context")
        assert res.status_code == 200
        ctx = res.json()["context"]
        assert "## Audio Analysis Context" in ctx
        assert "unavailable" in ctx
        assert "## Audio Analysis Instructions" not in ctx

    async def test_opted_in_with_failed_status_returns_unavailability_note(
        self,
        client,
        meetings_dir: Path,
        sample_audio: Path,
        base_metadata: dict,
        base_transcript: dict,
    ):
        base_metadata["audio_analysis_enabled"] = True
        audio_analysis = {
            "status": "failed",
            "reason": "model_load_error",
            "emotions": [],
            "prosody": [],
            "prosody_unavailable": [],
            "interactions": [],
            "segment_interactions": [],
            "dominant_speaker_limitation": False,
        }
        meeting_id = _write_meeting(meetings_dir, sample_audio, base_metadata, base_transcript, audio_analysis)

        res = await client.get(f"/api/meetings/{meeting_id}/analysis-context")
        assert res.status_code == 200
        ctx = res.json()["context"]
        assert "model_load_error" in ctx
        assert "## Audio Analysis Instructions" not in ctx

    async def test_opted_in_completed_returns_full_context_with_speaker_names(
        self,
        client,
        meetings_dir: Path,
        sample_audio: Path,
        base_metadata: dict,
        base_transcript: dict,
    ):
        base_metadata["audio_analysis_enabled"] = True
        # speakers in fixture: SPEAKER_00 -> Alice, SPEAKER_01 -> Bob
        audio_analysis = {
            "status": "completed",
            "emotion_status": "completed",
            "prosody_status": "completed",
            "interaction_status": "completed",
            "emotions": [
                {
                    "segment_id": "seg-001",
                    "speaker": "SPEAKER_00",
                    "start": 0.0,
                    "end": 5.2,
                    "primary_emotion": "engaged",
                    "confidence": 0.92,
                    "emotion_scores": {"engaged": 0.92},
                    "low_confidence": False,
                },
                {
                    "segment_id": "seg-003",
                    "speaker": "SPEAKER_00",
                    "start": 13.0,
                    "end": 20.1,
                    "primary_emotion": "frustrated",
                    "confidence": 0.81,
                    "emotion_scores": {"frustrated": 0.81},
                    "low_confidence": False,
                },
            ],
            "prosody": [],
            "prosody_unavailable": [],
            "interactions": [
                {
                    "event_type": "interruption",
                    "timestamp": 12.0,
                    "speaker_a": "SPEAKER_00",
                    "speaker_b": "SPEAKER_01",
                    "duration": 0.5,
                    "context": "",
                }
            ],
            "segment_interactions": [],
            "dominant_speaker_limitation": False,
        }
        # seg-003 = "Great, go ahead." — change to an agreement phrase to surface a mismatch.
        base_transcript["segments"][2]["text"] = "Sounds good to me."

        meeting_id = _write_meeting(meetings_dir, sample_audio, base_metadata, base_transcript, audio_analysis)

        res = await client.get(f"/api/meetings/{meeting_id}/analysis-context")
        assert res.status_code == 200
        ctx = res.json()["context"]
        assert "## Audio Analysis Context" in ctx
        assert "### Emotional Patterns" in ctx
        # speaker display names
        assert "Alice" in ctx
        assert "Bob" in ctx
        # word-tone mismatch
        assert "### Word-Tone Mismatches" in ctx
        assert "Sounds good to me." in ctx
        # interaction dynamics
        assert "### Interaction Dynamics" in ctx
        assert "Bob interrupted Alice 1 time" in ctx
        # template-agnostic instructions appended
        assert "## Audio Analysis Instructions" in ctx

    async def test_dominant_speaker_limitation_disclosed(
        self,
        client,
        meetings_dir: Path,
        sample_audio: Path,
        base_metadata: dict,
        base_transcript: dict,
    ):
        base_metadata["audio_analysis_enabled"] = True
        audio_analysis = {
            "status": "completed",
            "emotion_status": "completed",
            "interaction_status": "completed",
            "emotions": [
                {
                    "segment_id": "seg-001",
                    "speaker": "SPEAKER_00",
                    "start": 0.0,
                    "end": 5.2,
                    "primary_emotion": "engaged",
                    "confidence": 0.9,
                    "emotion_scores": {"engaged": 0.9},
                    "low_confidence": False,
                }
            ],
            "prosody": [],
            "prosody_unavailable": [],
            "interactions": [],
            "segment_interactions": [],
            "dominant_speaker_limitation": True,
        }
        meeting_id = _write_meeting(meetings_dir, sample_audio, base_metadata, base_transcript, audio_analysis)

        res = await client.get(f"/api/meetings/{meeting_id}/analysis-context")
        assert res.status_code == 200
        ctx = res.json()["context"]
        assert "single speaker dominates" in ctx
