from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from backend.schemas import EmotionAnnotation, EmotionCategory

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.5
SER_MODEL_ID = "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"
SAMPLE_RATE = 16000
MIN_SEGMENT_SECONDS = 0.3

# Model returns 7 labels; we collapse them into the 6 spec categories by
# summing scores within a category. No label maps to CONFIDENT — that
# category requires a model not yet available, so it will not appear in
# current outputs.
RAW_LABEL_TO_CATEGORY: dict[str, EmotionCategory] = {
    "angry": EmotionCategory.FRUSTRATED,
    "disgust": EmotionCategory.FRUSTRATED,
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


class _DirectClassifier:
    """Drop-in replacement for transformers.pipeline('audio-classification').

    The HF pipeline calls `import torchcodec` inside its preprocess step on
    every invocation, even when input is a pre-decoded numpy array. If the
    local torchcodec install is broken (a common state on macOS when torch
    and torchcodec drift apart), every classification raises. We bypass the
    pipeline entirely by calling the feature extractor and model directly.
    """

    def __init__(self, feature_extractor, model):
        import torch

        self._torch = torch
        self._feature_extractor = feature_extractor
        self._model = model
        self._labels = model.config.id2label

    def __call__(self, payload, top_k=None):
        chunk = payload["raw"] if isinstance(payload, dict) else payload
        sampling_rate = payload.get("sampling_rate", SAMPLE_RATE) if isinstance(payload, dict) else SAMPLE_RATE
        inputs = self._feature_extractor(chunk, sampling_rate=sampling_rate, return_tensors="pt")
        with self._torch.no_grad():
            logits = self._model(**inputs).logits
        probs = self._torch.nn.functional.softmax(logits, dim=-1)[0]
        return [{"label": self._labels[i], "score": float(probs[i])} for i in range(len(self._labels))]


def _load_classifier():
    """Lazy-load the SER model directly, bypassing transformers.pipeline."""
    from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

    feature_extractor = AutoFeatureExtractor.from_pretrained(SER_MODEL_ID)
    model = AutoModelForAudioClassification.from_pretrained(SER_MODEL_ID)
    model.eval()
    return _DirectClassifier(feature_extractor, model)


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
