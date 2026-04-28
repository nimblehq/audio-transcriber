from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from backend.schemas import EmotionAnnotation, EmotionCategory

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.5
SER_MODEL_ID = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
SAMPLE_RATE = 16000
MIN_SEGMENT_SECONDS = 0.3

# ehcalabres model returns these 8 labels; we collapse them into the 6 spec
# categories by summing scores within a category.
RAW_LABEL_TO_CATEGORY: dict[str, EmotionCategory] = {
    "angry": EmotionCategory.FRUSTRATED,
    "disgust": EmotionCategory.FRUSTRATED,
    "calm": EmotionCategory.CONFIDENT,
    "fearful": EmotionCategory.UNCERTAIN,
    "happy": EmotionCategory.ENGAGED,
    "surprised": EmotionCategory.ENGAGED,
    "neutral": EmotionCategory.NEUTRAL,
    "sad": EmotionCategory.DISENGAGED,
}


class _Segment(Protocol):
    id: str
    start: float
    end: float
    speaker: str


def _aggregate_scores(raw_scores: list[dict]) -> dict[EmotionCategory, float]:
    """Map raw model labels to spec categories and sum scores within each."""
    category_scores: dict[EmotionCategory, float] = {c: 0.0 for c in EmotionCategory}
    for entry in raw_scores:
        label = entry["label"].lower()
        category = RAW_LABEL_TO_CATEGORY.get(label)
        if category is None:
            continue
        category_scores[category] += float(entry["score"])
    return category_scores


def _classify_segment(classifier, audio_array, segment: _Segment) -> EmotionAnnotation | None:
    duration = segment.end - segment.start
    if duration < MIN_SEGMENT_SECONDS:
        return None

    start_idx = int(segment.start * SAMPLE_RATE)
    end_idx = int(segment.end * SAMPLE_RATE)
    chunk = audio_array[start_idx:end_idx]
    if len(chunk) == 0:
        return None

    raw_scores = classifier({"raw": chunk, "sampling_rate": SAMPLE_RATE}, top_k=None)
    if not raw_scores:
        return None

    category_scores = _aggregate_scores(raw_scores)
    primary_emotion = max(category_scores, key=category_scores.get)
    confidence = category_scores[primary_emotion]

    return EmotionAnnotation(
        segment_id=segment.id,
        speaker=segment.speaker,
        start=segment.start,
        end=segment.end,
        primary_emotion=primary_emotion,
        confidence=round(confidence, 4),
        emotion_scores={c.value: round(s, 4) for c, s in category_scores.items()},
        low_confidence=confidence < LOW_CONFIDENCE_THRESHOLD,
    )


def _load_classifier():
    """Lazy-load the HF audio-classification pipeline."""
    from transformers import pipeline

    return pipeline("audio-classification", model=SER_MODEL_ID)


def _load_audio(audio_path: Path):
    import whisperx

    return whisperx.load_audio(str(audio_path))


def analyze_segments(
    audio_path: Path,
    segments: Iterable[_Segment],
    classifier=None,
    audio_array=None,
) -> list[EmotionAnnotation]:
    """Run SER on each segment.

    `classifier` and `audio_array` are injectable for tests; production callers
    pass neither and the analyzer loads its own.
    """
    if classifier is None:
        classifier = _load_classifier()
    if audio_array is None:
        audio_array = _load_audio(audio_path)

    annotations: list[EmotionAnnotation] = []
    for segment in segments:
        try:
            annotation = _classify_segment(classifier, audio_array, segment)
        except Exception:
            logger.exception("Emotion classification failed for segment %s", segment.id)
            continue
        if annotation is not None:
            annotations.append(annotation)
    return annotations
