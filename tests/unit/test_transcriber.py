from __future__ import annotations

import json
import struct
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.schemas import AudioAnalysisStatus, JobStatus, MeetingStatus
from backend.services.job_queue import JobQueue
from backend.services.transcriber import _get_device, _is_cancelled, _run_audio_analysis


def _create_test_audio(path: Path) -> None:
    """Create a minimal valid WAV file for testing."""
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(struct.pack("<" + "h" * 16, *([0] * 16)))


def _create_meeting_on_disk(
    meetings_dir: Path,
    meeting_id: str = "test-meeting",
    status: str = "processing",
    audio_filename: str = "audio.wav",
    language: str = "auto",
    num_speakers: int | None = None,
) -> Path:
    """Create a meeting directory with metadata and audio file."""
    meeting_dir = meetings_dir / meeting_id
    meeting_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "id": meeting_id,
        "title": "Test Meeting",
        "type": "other",
        "status": status,
        "audio_filename": audio_filename,
        "language": language,
        "num_speakers": num_speakers,
        "preprocess_audio": False,
        "created_at": "2026-03-14T00:00:00",
        "speakers": {},
    }
    (meeting_dir / "metadata.json").write_text(json.dumps(metadata))
    _create_test_audio(meeting_dir / audio_filename)

    return meeting_dir


class TestIsCancelled:
    def test_returns_false_when_processing(self, tmp_path: Path):
        meta = {"id": "m1", "title": "Test", "status": "processing", "audio_filename": "a.wav"}
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps(meta))

        assert _is_cancelled(meta_path) is False

    def test_returns_true_when_error(self, tmp_path: Path):
        meta = {"id": "m1", "title": "Test", "status": "error", "audio_filename": "a.wav"}
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps(meta))

        assert _is_cancelled(meta_path) is True

    def test_returns_true_when_ready(self, tmp_path: Path):
        meta = {"id": "m1", "title": "Test", "status": "ready", "audio_filename": "a.wav"}
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps(meta))

        assert _is_cancelled(meta_path) is True

    def test_returns_false_on_read_error(self, tmp_path: Path):
        meta_path = tmp_path / "nonexistent.json"
        assert _is_cancelled(meta_path) is False


class TestGetDevice:
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cuda")
    def test_returns_configured_device(self):
        assert _get_device() == "cuda"

    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    def test_returns_cpu_when_configured(self):
        assert _get_device() == "cpu"

    @patch("backend.services.transcriber.WHISPER_DEVICE", "auto")
    def test_auto_falls_back_to_cpu_without_torch(self):
        with patch.dict("sys.modules", {"torch": None}):
            assert _get_device() == "cpu"

    @patch("backend.services.transcriber.WHISPER_DEVICE", "auto")
    def test_auto_detects_cuda(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        with patch.dict("sys.modules", {"torch": mock_torch}):
            assert _get_device() == "cuda"

    @patch("backend.services.transcriber.WHISPER_DEVICE", "auto")
    def test_auto_returns_cpu_when_no_cuda(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        with patch.dict("sys.modules", {"torch": mock_torch}):
            assert _get_device() == "cpu"


class TestRunTranscription:
    """Tests for _run_transcription with all ML dependencies mocked."""

    def _build_mocks(self):
        """Create mock objects for whisperx and torch."""
        mock_whisperx = MagicMock()
        mock_whisperx.load_audio.return_value = MagicMock()
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {"start": 0.0, "end": 1.5, "text": " Hello there.", "speaker": "SPEAKER_00"},
                {"start": 1.5, "end": 3.0, "text": " How are you?", "speaker": "SPEAKER_01"},
            ],
            "language": "en",
        }
        mock_whisperx.load_model.return_value = mock_model
        mock_whisperx.load_align_model.return_value = (MagicMock(), MagicMock())
        mock_whisperx.align.return_value = {
            "segments": [
                {"start": 0.0, "end": 1.5, "text": " Hello there.", "speaker": "SPEAKER_00"},
                {"start": 1.5, "end": 3.0, "text": " How are you?", "speaker": "SPEAKER_01"},
            ],
        }

        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        mock_diarize_pipeline = MagicMock()
        mock_assign_speakers = MagicMock(
            return_value={
                "segments": [
                    {"start": 0.0, "end": 1.5, "text": " Hello there.", "speaker": "SPEAKER_00"},
                    {"start": 1.5, "end": 3.0, "text": " How are you?", "speaker": "SPEAKER_01"},
                ],
            }
        )

        return mock_whisperx, mock_torch, mock_diarize_pipeline, mock_assign_speakers

    @patch("backend.services.transcriber.WHISPER_BATCH_SIZE", 16)
    @patch("backend.services.transcriber.WHISPER_MODEL", "large-v3")
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    @patch("backend.services.transcriber.HF_TOKEN", "test-token")
    def test_happy_path_writes_transcript_and_updates_metadata(self, tmp_path: Path):
        mock_whisperx, mock_torch, mock_diarize_cls, mock_assign = self._build_mocks()
        queue = JobQueue()
        meetings_dir = tmp_path / "meetings"
        meeting_dir = _create_meeting_on_disk(meetings_dir)
        job = queue.create_job("test-meeting")

        with (
            patch("backend.services.transcriber.MEETINGS_DIR", meetings_dir),
            patch("backend.services.transcriber.job_queue", queue),
            patch.dict(
                "sys.modules",
                {
                    "whisperx": mock_whisperx,
                    "torch": mock_torch,
                    "whisperx.diarize": MagicMock(
                        DiarizationPipeline=mock_diarize_cls,
                        assign_word_speakers=mock_assign,
                    ),
                    "functools": __import__("functools"),
                    "warnings": __import__("warnings"),
                },
            ),
        ):
            from backend.services.transcriber import _run_transcription

            _run_transcription("test-meeting", job.id)

        # Verify transcript written
        transcript_path = meeting_dir / "transcript.json"
        assert transcript_path.exists()
        transcript = json.loads(transcript_path.read_text())
        assert len(transcript["segments"]) == 2
        assert transcript["segments"][0]["text"] == "Hello there."
        assert transcript["segments"][0]["speaker"] == "SPEAKER_00"
        assert transcript["language"] == "en"

        # Verify metadata updated to READY
        metadata = json.loads((meeting_dir / "metadata.json").read_text())
        assert metadata["status"] == MeetingStatus.READY.value
        assert metadata["duration_seconds"] == 3.0
        assert "SPEAKER_00" in metadata["speakers"]
        assert "SPEAKER_01" in metadata["speakers"]

        # Verify job completed
        updated_job = queue.get_job(job.id)
        assert updated_job.status == JobStatus.COMPLETED
        assert updated_job.progress == 100

    @patch("backend.services.transcriber.WHISPER_BATCH_SIZE", 16)
    @patch("backend.services.transcriber.WHISPER_MODEL", "large-v3")
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    @patch("backend.services.transcriber.HF_TOKEN", "")
    def test_skips_diarization_without_hf_token(self, tmp_path: Path):
        mock_whisperx, mock_torch, mock_diarize_cls, mock_assign = self._build_mocks()
        queue = JobQueue()
        meetings_dir = tmp_path / "meetings"
        _create_meeting_on_disk(meetings_dir)
        job = queue.create_job("test-meeting")

        with (
            patch("backend.services.transcriber.MEETINGS_DIR", meetings_dir),
            patch("backend.services.transcriber.job_queue", queue),
            patch.dict(
                "sys.modules",
                {
                    "whisperx": mock_whisperx,
                    "torch": mock_torch,
                    "whisperx.diarize": MagicMock(
                        DiarizationPipeline=mock_diarize_cls,
                        assign_word_speakers=mock_assign,
                    ),
                    "functools": __import__("functools"),
                    "warnings": __import__("warnings"),
                },
            ),
        ):
            from backend.services.transcriber import _run_transcription

            _run_transcription("test-meeting", job.id)

        # Diarization pipeline should not be called
        mock_diarize_cls.assert_not_called()

    @patch("backend.services.transcriber.WHISPER_BATCH_SIZE", 16)
    @patch("backend.services.transcriber.WHISPER_MODEL", "large-v3")
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    @patch("backend.services.transcriber.HF_TOKEN", "")
    def test_error_sets_job_failed_and_updates_metadata(self, tmp_path: Path):
        mock_whisperx = MagicMock()
        mock_whisperx.load_audio.side_effect = RuntimeError("Audio file corrupt")
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        queue = JobQueue()
        meetings_dir = tmp_path / "meetings"
        meeting_dir = _create_meeting_on_disk(meetings_dir)
        job = queue.create_job("test-meeting")

        with (
            patch("backend.services.transcriber.MEETINGS_DIR", meetings_dir),
            patch("backend.services.transcriber.job_queue", queue),
            patch.dict(
                "sys.modules",
                {
                    "whisperx": mock_whisperx,
                    "torch": mock_torch,
                    "whisperx.diarize": MagicMock(),
                    "functools": __import__("functools"),
                    "warnings": __import__("warnings"),
                },
            ),
        ):
            from backend.services.transcriber import _run_transcription

            _run_transcription("test-meeting", job.id)

        # Job should be FAILED
        updated_job = queue.get_job(job.id)
        assert updated_job.status == JobStatus.FAILED
        assert "Audio file corrupt" in updated_job.error

        # Metadata should have error status
        metadata = json.loads((meeting_dir / "metadata.json").read_text())
        assert metadata["status"] == "error"
        assert "Audio file corrupt" in metadata["error"]

    @patch("backend.services.transcriber.WHISPER_BATCH_SIZE", 16)
    @patch("backend.services.transcriber.WHISPER_MODEL", "large-v3")
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    @patch("backend.services.transcriber.HF_TOKEN", "")
    def test_discards_results_when_cancelled(self, tmp_path: Path):
        mock_whisperx, mock_torch, mock_diarize_cls, mock_assign = self._build_mocks()
        queue = JobQueue()
        meetings_dir = tmp_path / "meetings"
        meeting_dir = _create_meeting_on_disk(meetings_dir)
        job = queue.create_job("test-meeting")

        # Change status to "error" before saving results to simulate cancellation
        def cancel_before_save(*args, **kwargs):
            meta = json.loads((meeting_dir / "metadata.json").read_text())
            meta["status"] = "error"
            (meeting_dir / "metadata.json").write_text(json.dumps(meta))
            return mock_whisperx.align.return_value

        # Make align trigger the cancellation
        mock_whisperx.align.side_effect = cancel_before_save

        with (
            patch("backend.services.transcriber.MEETINGS_DIR", meetings_dir),
            patch("backend.services.transcriber.job_queue", queue),
            patch.dict(
                "sys.modules",
                {
                    "whisperx": mock_whisperx,
                    "torch": mock_torch,
                    "whisperx.diarize": MagicMock(
                        DiarizationPipeline=mock_diarize_cls,
                        assign_word_speakers=mock_assign,
                    ),
                    "functools": __import__("functools"),
                    "warnings": __import__("warnings"),
                },
            ),
        ):
            from backend.services.transcriber import _run_transcription

            _run_transcription("test-meeting", job.id)

        # Transcript should NOT be written
        assert not (meeting_dir / "transcript.json").exists()

    @patch("backend.services.transcriber.WHISPER_BATCH_SIZE", 16)
    @patch("backend.services.transcriber.WHISPER_MODEL", "large-v3")
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    @patch("backend.services.transcriber.HF_TOKEN", "")
    def test_no_speech_detected_raises_error(self, tmp_path: Path):
        mock_whisperx = MagicMock()
        mock_whisperx.load_audio.return_value = MagicMock()
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"segments": [], "language": "en"}
        mock_whisperx.load_model.return_value = mock_model
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        queue = JobQueue()
        meetings_dir = tmp_path / "meetings"
        _create_meeting_on_disk(meetings_dir)
        job = queue.create_job("test-meeting")

        with (
            patch("backend.services.transcriber.MEETINGS_DIR", meetings_dir),
            patch("backend.services.transcriber.job_queue", queue),
            patch.dict(
                "sys.modules",
                {
                    "whisperx": mock_whisperx,
                    "torch": mock_torch,
                    "whisperx.diarize": MagicMock(),
                    "functools": __import__("functools"),
                    "warnings": __import__("warnings"),
                },
            ),
        ):
            from backend.services.transcriber import _run_transcription

            _run_transcription("test-meeting", job.id)

        updated_job = queue.get_job(job.id)
        assert updated_job.status == JobStatus.FAILED
        assert "No speech detected" in updated_job.error

    @patch("backend.services.transcriber.WHISPER_BATCH_SIZE", 16)
    @patch("backend.services.transcriber.WHISPER_MODEL", "large-v3")
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    @patch("backend.services.transcriber.HF_TOKEN", "")
    def test_thai_alignment_uses_custom_model(self, tmp_path: Path):
        mock_whisperx, mock_torch, mock_diarize_cls, mock_assign = self._build_mocks()
        mock_model = mock_whisperx.load_model.return_value
        mock_model.transcribe.return_value["language"] = "th"

        queue = JobQueue()
        meetings_dir = tmp_path / "meetings"
        _create_meeting_on_disk(meetings_dir, language="auto")
        job = queue.create_job("test-meeting")

        with (
            patch("backend.services.transcriber.MEETINGS_DIR", meetings_dir),
            patch("backend.services.transcriber.job_queue", queue),
            patch.dict(
                "sys.modules",
                {
                    "whisperx": mock_whisperx,
                    "torch": mock_torch,
                    "whisperx.diarize": MagicMock(
                        DiarizationPipeline=mock_diarize_cls,
                        assign_word_speakers=mock_assign,
                    ),
                    "functools": __import__("functools"),
                    "warnings": __import__("warnings"),
                },
            ),
        ):
            from backend.services.transcriber import _run_transcription

            _run_transcription("test-meeting", job.id)

        mock_whisperx.load_align_model.assert_called_once_with(
            language_code="th",
            device="cpu",
            model_name="airesearch/wav2vec2-large-xlsr-53-th",
        )

    @patch("backend.services.transcriber.WHISPER_BATCH_SIZE", 16)
    @patch("backend.services.transcriber.WHISPER_MODEL", "large-v3")
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    @patch("backend.services.transcriber.HF_TOKEN", "")
    def test_unsupported_language_skips_alignment(self, tmp_path: Path):
        mock_whisperx, mock_torch, mock_diarize_cls, mock_assign = self._build_mocks()
        mock_model = mock_whisperx.load_model.return_value
        mock_model.transcribe.return_value["language"] = "xx"

        queue = JobQueue()
        meetings_dir = tmp_path / "meetings"
        _create_meeting_on_disk(meetings_dir, language="auto")
        job = queue.create_job("test-meeting")

        with (
            patch("backend.services.transcriber.MEETINGS_DIR", meetings_dir),
            patch("backend.services.transcriber.job_queue", queue),
            patch.dict(
                "sys.modules",
                {
                    "whisperx": mock_whisperx,
                    "torch": mock_torch,
                    "whisperx.diarize": MagicMock(
                        DiarizationPipeline=mock_diarize_cls,
                        assign_word_speakers=mock_assign,
                    ),
                    "functools": __import__("functools"),
                    "warnings": __import__("warnings"),
                },
            ),
        ):
            from backend.services.transcriber import _run_transcription

            _run_transcription("test-meeting", job.id)

        mock_whisperx.load_align_model.assert_not_called()

    @patch("backend.services.transcriber.WHISPER_BATCH_SIZE", 16)
    @patch("backend.services.transcriber.WHISPER_MODEL", "large-v3")
    @patch("backend.services.transcriber.WHISPER_DEVICE", "cpu")
    @patch("backend.services.transcriber.HF_TOKEN", "")
    def test_english_alignment_uses_default_model(self, tmp_path: Path):
        mock_whisperx, mock_torch, mock_diarize_cls, mock_assign = self._build_mocks()

        queue = JobQueue()
        meetings_dir = tmp_path / "meetings"
        _create_meeting_on_disk(meetings_dir, language="auto")
        job = queue.create_job("test-meeting")

        with (
            patch("backend.services.transcriber.MEETINGS_DIR", meetings_dir),
            patch("backend.services.transcriber.job_queue", queue),
            patch.dict(
                "sys.modules",
                {
                    "whisperx": mock_whisperx,
                    "torch": mock_torch,
                    "whisperx.diarize": MagicMock(
                        DiarizationPipeline=mock_diarize_cls,
                        assign_word_speakers=mock_assign,
                    ),
                    "functools": __import__("functools"),
                    "warnings": __import__("warnings"),
                },
            ),
        ):
            from backend.services.transcriber import _run_transcription

            _run_transcription("test-meeting", job.id)

        mock_whisperx.load_align_model.assert_called_once_with(
            language_code="en",
            device="cpu",
            model_name=None,
        )


class TestStartTranscription:
    def test_spawns_daemon_thread(self):
        with patch("backend.services.transcriber._run_transcription") as mock_run:
            from backend.services.transcriber import start_transcription

            start_transcription("m1", "j1")

            # Give the thread a moment to start
            import time

            time.sleep(0.05)

            mock_run.assert_called_once_with("m1", "j1")


class TestRunAudioAnalysis:
    """Covers the inline call site that the analyzer unit tests don't exercise."""

    def _segments(self):
        return [
            {"id": "seg_0000", "start": 0.0, "end": 1.0, "speaker": "SPEAKER_00", "text": "hi"},
        ]

    def test_unsupported_language_skips_emotion_but_runs_prosody(self):
        with patch("backend.services.prosody_analyzer.analyze_segments", return_value=([], [])) as mock_prosody:
            with patch("backend.services.transcriber.job_queue.update_job"):
                result = _run_audio_analysis(
                    job_id="j1", audio=MagicMock(), segments=self._segments(), detected_language="fr"
                )
        # Emotions skipped (English-only), prosody ran (language-agnostic, BR-2.1)
        assert result.emotion_status == AudioAnalysisStatus.UNAVAILABLE
        assert result.emotion_reason == "language_not_supported:fr"
        assert result.prosody_status == AudioAnalysisStatus.COMPLETED
        # Pipeline status rolls up — completes when at least one stage produces output
        assert result.status == AudioAnalysisStatus.COMPLETED
        mock_prosody.assert_called_once()

    def test_english_runs_both_stages_and_returns_completed(self):
        with patch("backend.services.emotion_analyzer.analyze_segments", return_value=[]) as mock_emotion:
            with patch("backend.services.prosody_analyzer.analyze_segments", return_value=([], [])) as mock_prosody:
                with patch("backend.services.transcriber.job_queue.update_job"):
                    result = _run_audio_analysis(
                        job_id="j1",
                        audio=MagicMock(),
                        segments=self._segments(),
                        detected_language="en",
                    )
        assert result.status == AudioAnalysisStatus.COMPLETED
        assert result.emotion_status == AudioAnalysisStatus.COMPLETED
        assert result.prosody_status == AudioAnalysisStatus.COMPLETED
        mock_emotion.assert_called_once()
        mock_prosody.assert_called_once()

    def test_emotion_failure_does_not_block_prosody(self):
        with patch(
            "backend.services.emotion_analyzer.analyze_segments",
            side_effect=RuntimeError("model crashed"),
        ):
            with patch("backend.services.prosody_analyzer.analyze_segments", return_value=([], [])):
                with patch("backend.services.transcriber.job_queue.update_job"):
                    result = _run_audio_analysis(
                        job_id="j1",
                        audio=MagicMock(),
                        segments=self._segments(),
                        detected_language="en",
                    )
        # Emotion failed but prosody completed → overall COMPLETED
        assert result.emotion_status == AudioAnalysisStatus.FAILED
        assert "model crashed" in result.emotion_reason
        assert result.prosody_status == AudioAnalysisStatus.COMPLETED
        assert result.status == AudioAnalysisStatus.COMPLETED

    def test_prosody_failure_does_not_block_emotion(self):
        with patch("backend.services.emotion_analyzer.analyze_segments", return_value=[]):
            with patch(
                "backend.services.prosody_analyzer.analyze_segments",
                side_effect=RuntimeError("praat crashed"),
            ):
                with patch("backend.services.transcriber.job_queue.update_job"):
                    result = _run_audio_analysis(
                        job_id="j1",
                        audio=MagicMock(),
                        segments=self._segments(),
                        detected_language="en",
                    )
        assert result.prosody_status == AudioAnalysisStatus.FAILED
        assert "praat crashed" in result.prosody_reason
        assert result.emotion_status == AudioAnalysisStatus.COMPLETED
        assert result.status == AudioAnalysisStatus.COMPLETED

    def test_both_stages_fail_rolls_up_to_failed(self):
        with patch(
            "backend.services.emotion_analyzer.analyze_segments",
            side_effect=RuntimeError("emotion boom"),
        ):
            with patch(
                "backend.services.prosody_analyzer.analyze_segments",
                side_effect=RuntimeError("prosody boom"),
            ):
                with patch("backend.services.transcriber.job_queue.update_job"):
                    result = _run_audio_analysis(
                        job_id="j1",
                        audio=MagicMock(),
                        segments=self._segments(),
                        detected_language="en",
                    )
        assert result.status == AudioAnalysisStatus.FAILED
        assert result.emotion_status == AudioAnalysisStatus.FAILED
        assert result.prosody_status == AudioAnalysisStatus.FAILED

    def test_prosody_unavailable_markers_propagated(self):
        from backend.schemas import ProsodyUnavailable

        with patch("backend.services.emotion_analyzer.analyze_segments", return_value=[]):
            with patch(
                "backend.services.prosody_analyzer.analyze_segments",
                return_value=([], [ProsodyUnavailable(segment_id="seg_0000", reason="non_speech")]),
            ):
                with patch("backend.services.transcriber.job_queue.update_job"):
                    result = _run_audio_analysis(
                        job_id="j1",
                        audio=MagicMock(),
                        segments=self._segments(),
                        detected_language="en",
                    )
        assert len(result.prosody_unavailable) == 1
        assert result.prosody_unavailable[0].reason == "non_speech"
