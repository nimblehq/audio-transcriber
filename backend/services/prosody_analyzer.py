from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Protocol

from backend.schemas import ProsodyAnnotation, ProsodyUnavailable

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
MIN_SEGMENT_SECONDS = 0.3

# Non-speech detection: a segment is excluded if its raw RMS sits below this
# floor AND Praat's pitch tracker yielded zero voiced frames. Catches silence,
# extended pauses, and hold tones reliably; pure music is rare in meeting
# recordings and would still be reported as non-speech if it carries no pitch.
NON_SPEECH_RMS_FLOOR = 1e-3

# Pause detection: an intra-segment frame counts as silence when its RMS is
# below this fraction of the segment's peak RMS. Tuned to capture deliberate
# pauses while ignoring envelope ripple inside running speech.
PAUSE_RMS_RATIO = 0.1
PAUSE_FRAME_DURATION = 0.025  # 25 ms frames

REASON_NON_SPEECH = "non_speech"
REASON_EXTRACTION_FAILED = "prosody_unavailable"
REASON_TOO_SHORT = "too_short"


class _Segment(Protocol):
    id: str
    start: float
    end: float
    speaker: str
    text: str


def _compute_rms(chunk):
    import numpy as np

    arr = np.asarray(chunk, dtype=np.float64)
    if arr.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(arr * arr)))


def _compute_pitch_stats(chunk, sampling_rate: int) -> tuple[float, float, int]:
    """Return (mean Hz, variance Hz^2, voiced_frame_count) using Praat."""
    import numpy as np
    import parselmouth

    arr = np.asarray(chunk, dtype=np.float64)
    if arr.size == 0:
        return 0.0, 0.0, 0
    sound = parselmouth.Sound(arr, sampling_frequency=sampling_rate)
    pitch = sound.to_pitch()
    freqs = pitch.selected_array["frequency"]
    voiced = freqs[freqs > 0]
    if voiced.size == 0:
        return 0.0, 0.0, 0
    return float(np.mean(voiced)), float(np.var(voiced)), int(voiced.size)


def _compute_pause_ratio(chunk, sampling_rate: int) -> float:
    """Fraction of the segment that's below the pause RMS threshold."""
    import numpy as np

    arr = np.asarray(chunk, dtype=np.float64)
    if arr.size == 0:
        return 0.0

    frame_len = max(1, int(sampling_rate * PAUSE_FRAME_DURATION))
    n_frames = arr.size // frame_len
    if n_frames == 0:
        return 0.0

    trimmed = arr[: n_frames * frame_len].reshape(n_frames, frame_len)
    frame_rms = np.sqrt(np.mean(trimmed * trimmed, axis=1))
    peak = float(frame_rms.max())
    if peak <= 0:
        return 1.0
    threshold = peak * PAUSE_RMS_RATIO
    silent = int(np.sum(frame_rms < threshold))
    return silent / n_frames


def _compute_speaking_rate(text: str, duration: float) -> float:
    if duration <= 0:
        return 0.0
    word_count = len(text.split())
    return word_count / duration * 60.0


class _RawFeatures:
    __slots__ = (
        "segment_id",
        "speaker",
        "start",
        "end",
        "rms",
        "pitch_mean",
        "pitch_variance",
        "voiced_frames",
        "speaking_rate",
        "pause_ratio",
        "frame_rms",
    )

    def __init__(
        self,
        segment_id: str,
        speaker: str,
        start: float,
        end: float,
        rms: float,
        pitch_mean: float,
        pitch_variance: float,
        voiced_frames: int,
        speaking_rate: float,
        pause_ratio: float,
        frame_rms,
    ):
        self.segment_id = segment_id
        self.speaker = speaker
        self.start = start
        self.end = end
        self.rms = rms
        self.pitch_mean = pitch_mean
        self.pitch_variance = pitch_variance
        self.voiced_frames = voiced_frames
        self.speaking_rate = speaking_rate
        self.pause_ratio = pause_ratio
        self.frame_rms = frame_rms


class _TooShort:
    """Sentinel: segment was too short to extract features from."""


def _extract_segment_features(audio_array, segment: _Segment, sampling_rate: int):
    """Extract raw (un-normalized) features for one segment.

    Returns `_RawFeatures` on success or the `_TooShort` sentinel when the
    segment is below the analyzable duration. The sentinel lets the caller
    record an unavailable marker so every segment has either prosody data
    or an explicit explanation (story #50 truth).
    """
    import numpy as np

    duration = segment.end - segment.start
    if duration < MIN_SEGMENT_SECONDS:
        return _TooShort

    start_idx = int(segment.start * sampling_rate)
    end_idx = int(segment.end * sampling_rate)
    chunk = np.asarray(audio_array, dtype=np.float64)[start_idx:end_idx]
    if chunk.size == 0:
        return _TooShort

    rms = _compute_rms(chunk)

    # Frame-level RMS for pause ratio and to expose for non-speech detection
    frame_len = max(1, int(sampling_rate * PAUSE_FRAME_DURATION))
    n_frames = chunk.size // frame_len
    if n_frames > 0:
        trimmed = chunk[: n_frames * frame_len].reshape(n_frames, frame_len)
        frame_rms = np.sqrt(np.mean(trimmed * trimmed, axis=1))
    else:
        frame_rms = np.array([rms])

    pitch_mean, pitch_variance, voiced_frames = _compute_pitch_stats(chunk, sampling_rate)
    pause_ratio = _compute_pause_ratio(chunk, sampling_rate)
    speaking_rate = _compute_speaking_rate(segment.text, duration)

    return _RawFeatures(
        segment_id=segment.id,
        speaker=segment.speaker,
        start=segment.start,
        end=segment.end,
        rms=rms,
        pitch_mean=pitch_mean,
        pitch_variance=pitch_variance,
        voiced_frames=voiced_frames,
        speaking_rate=speaking_rate,
        pause_ratio=pause_ratio,
        frame_rms=frame_rms,
    )


def _is_non_speech(features: _RawFeatures) -> bool:
    return features.rms < NON_SPEECH_RMS_FLOOR and features.voiced_frames == 0


def _normalize_volume(features: list[_RawFeatures]) -> dict[str, tuple[float, float]]:
    """Compute meeting-wide normalized (volume_mean, volume_variance) per segment."""
    import numpy as np

    if not features:
        return {}

    peak = max(f.rms for f in features)
    if peak <= 0:
        return {f.segment_id: (0.0, 0.0) for f in features}

    out: dict[str, tuple[float, float]] = {}
    for f in features:
        normalized_frame_rms = np.asarray(f.frame_rms, dtype=np.float64) / peak
        volume_mean = float(np.mean(normalized_frame_rms))
        volume_variance = float(np.var(normalized_frame_rms))
        out[f.segment_id] = (volume_mean, volume_variance)
    return out


def analyze_segments(
    audio_array,
    segments: Iterable[_Segment],
    sampling_rate: int = SAMPLE_RATE,
) -> tuple[list[ProsodyAnnotation], list[ProsodyUnavailable]]:
    """Run prosodic feature extraction on each segment.

    Returns a tuple of (prosody annotations, unavailable markers). Per-segment
    failures are isolated — a single broken segment does not abort the batch.
    Non-speech segments are reported as unavailable rather than producing
    noise-level prosody values.
    """
    raw: list[_RawFeatures] = []
    unavailable: list[ProsodyUnavailable] = []

    for segment in segments:
        try:
            features = _extract_segment_features(audio_array, segment, sampling_rate)
        except Exception:
            logger.exception("Prosody extraction failed for segment %s", segment.id)
            unavailable.append(ProsodyUnavailable(segment_id=segment.id, reason=REASON_EXTRACTION_FAILED))
            continue

        if features is _TooShort:
            unavailable.append(ProsodyUnavailable(segment_id=segment.id, reason=REASON_TOO_SHORT))
            continue

        if _is_non_speech(features):
            unavailable.append(ProsodyUnavailable(segment_id=segment.id, reason=REASON_NON_SPEECH))
            continue

        raw.append(features)

    normalized = _normalize_volume(raw)

    annotations: list[ProsodyAnnotation] = []
    for f in raw:
        volume_mean, volume_variance = normalized.get(f.segment_id, (0.0, 0.0))
        annotations.append(
            ProsodyAnnotation(
                segment_id=f.segment_id,
                speaker=f.speaker,
                start=f.start,
                end=f.end,
                volume_mean=round(volume_mean, 4),
                volume_variance=round(volume_variance, 6),
                pitch_mean=round(f.pitch_mean, 2),
                pitch_variance=round(f.pitch_variance, 2),
                speaking_rate=round(f.speaking_rate, 2),
                pause_ratio=round(f.pause_ratio, 4),
            )
        )

    return annotations, unavailable
