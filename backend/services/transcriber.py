from __future__ import annotations

import json
import logging
import threading

from backend.schemas import JobStatus, MeetingMetadata, MeetingStatus
from backend.services.job_queue import job_queue
from config import HF_TOKEN, MEETINGS_DIR, WHISPER_BATCH_SIZE, WHISPER_DEVICE, WHISPER_MODEL

logger = logging.getLogger(__name__)


def _get_device() -> str:
    if WHISPER_DEVICE != "auto":
        return WHISPER_DEVICE
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def _run_transcription(meeting_id: str, job_id: str):
    """Run transcription in a background thread."""
    meeting_dir = MEETINGS_DIR / meeting_id
    metadata_path = meeting_dir / "metadata.json"

    try:
        with open(metadata_path) as f:
            metadata = MeetingMetadata(**json.load(f))

        audio_path = meeting_dir / metadata.audio_filename

        job_queue.update_job(job_id, status=JobStatus.PROCESSING, stage="transcribing", progress=10)

        # Import heavy deps only when needed
        import warnings
        warnings.filterwarnings("ignore", message="Model was trained with")
        warnings.filterwarnings("ignore", message="torchaudio._backend.list_audio_backends")

        import functools

        import torch

        # PyTorch 2.6+ compat patch
        _original_torch_load = torch.load

        @functools.wraps(_original_torch_load)
        def _patched_torch_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return _original_torch_load(*args, **kwargs)

        torch.load = _patched_torch_load

        import whisperx
        from whisperx.diarize import DiarizationPipeline, assign_word_speakers

        device = _get_device()
        compute_type = "float16" if device == "cuda" else "float32"
        batch_size = WHISPER_BATCH_SIZE if device == "cuda" else 4

        # Load audio
        audio = whisperx.load_audio(str(audio_path))

        # Transcribe
        job_queue.update_job(job_id, stage="transcribing", progress=20)
        model = whisperx.load_model(WHISPER_MODEL, device, compute_type=compute_type)
        transcribe_opts = {"batch_size": batch_size}
        if metadata.language and metadata.language != "auto":
            transcribe_opts["language"] = metadata.language
        result = model.transcribe(audio, **transcribe_opts)

        if not result or not result.get("segments"):
            raise RuntimeError("No speech detected in audio")

        detected_language = result.get("language", "unknown")

        del model
        if device == "cuda":
            torch.cuda.empty_cache()

        # Align
        ALIGNMENT_LANGUAGES = {
            "en", "fr", "de", "es", "it", "ja", "zh", "nl", "uk", "pt",
            "ar", "cs", "ru", "pl", "hu", "fi", "fa", "el", "tr", "da",
            "he", "vi", "ko", "ur", "te", "hi", "ta", "id", "ms"
        }

        if detected_language in ALIGNMENT_LANGUAGES:
            job_queue.update_job(job_id, stage="aligning", progress=50)
            model_a, align_metadata = whisperx.load_align_model(
                language_code=detected_language, device=device
            )
            result = whisperx.align(
                result["segments"], model_a, align_metadata, audio, device,
                return_char_alignments=False,
            )
            del model_a
            if device == "cuda":
                torch.cuda.empty_cache()

        # Diarize
        if HF_TOKEN:
            job_queue.update_job(job_id, stage="diarizing", progress=70)
            diarize_model = DiarizationPipeline(
                model_name="pyannote/speaker-diarization-3.1",
                token=HF_TOKEN,
                device=device,
            )
            diarize_kwargs = {}
            if metadata.num_speakers:
                diarize_kwargs["num_speakers"] = metadata.num_speakers
            diarize_segments = diarize_model(audio, **diarize_kwargs)
            result = assign_word_speakers(diarize_segments, result)

        job_queue.update_job(job_id, progress=90, stage="saving")

        # Build transcript
        segments = []
        for i, seg in enumerate(result["segments"]):
            segments.append({
                "id": f"seg_{i:04d}",
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "speaker": seg.get("speaker", "UNKNOWN"),
                "text": seg["text"].strip(),
            })

        transcript = {
            "segments": segments,
            "language": detected_language,
        }

        # Save transcript
        transcript_path = meeting_dir / "transcript.json"
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)

        # Update metadata
        duration = segments[-1]["end"] if segments else 0
        unique_speakers = sorted(set(s["speaker"] for s in segments))
        speaker_map = {spk: spk for spk in unique_speakers}

        metadata.status = MeetingStatus.READY
        metadata.duration_seconds = duration
        metadata.speakers = speaker_map

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata.model_dump(mode="json"), f, ensure_ascii=False, indent=2, default=str)

        job_queue.update_job(job_id, status=JobStatus.COMPLETED, progress=100, stage="done")

    except Exception as e:
        logger.exception("Transcription failed for meeting %s", meeting_id)
        job_queue.update_job(job_id, status=JobStatus.FAILED, error=str(e))

        # Update meeting status to error
        try:
            with open(metadata_path) as f:
                meta = json.load(f)
            meta["status"] = "error"
            with open(metadata_path, "w") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def start_transcription(meeting_id: str, job_id: str):
    """Start transcription in a background thread."""
    thread = threading.Thread(
        target=_run_transcription,
        args=(meeting_id, job_id),
        daemon=True,
    )
    thread.start()
