from __future__ import annotations

import numpy as np
import pytest

from backend.schemas import EmotionCategory, TranscriptSegment
from backend.services.emotion_analyzer import (
    LOW_CONFIDENCE_THRESHOLD,
    RAW_LABEL_TO_CATEGORY,
    _aggregate_scores,
    analyze_segments,
)


class FakeClassifier:
    """Stand-in for the HF audio-classification pipeline."""

    def __init__(self, scores_per_call):
        self._calls = list(scores_per_call)
        self.invocations = 0

    def __call__(self, payload, top_k=None):
        self.invocations += 1
        return self._calls.pop(0)


def _high_engaged_scores():
    return [
        {"label": "happy", "score": 0.7},
        {"label": "surprised", "score": 0.15},
        {"label": "neutral", "score": 0.05},
        {"label": "sad", "score": 0.04},
        {"label": "calm", "score": 0.03},
        {"label": "angry", "score": 0.02},
        {"label": "fearful", "score": 0.005},
        {"label": "disgust", "score": 0.005},
    ]


def _ambiguous_scores():
    return [
        {"label": "neutral", "score": 0.25},
        {"label": "calm", "score": 0.2},
        {"label": "sad", "score": 0.15},
        {"label": "happy", "score": 0.15},
        {"label": "surprised", "score": 0.1},
        {"label": "fearful", "score": 0.1},
        {"label": "angry", "score": 0.03},
        {"label": "disgust", "score": 0.02},
    ]


@pytest.fixture
def audio():
    return np.zeros(16000 * 10, dtype=np.float32)


@pytest.fixture
def segments():
    return [
        TranscriptSegment(id="s0", start=0.0, end=2.0, speaker="SPEAKER_00", text="hi"),
        TranscriptSegment(id="s1", start=2.0, end=4.0, speaker="SPEAKER_01", text="hey"),
    ]


class TestRawLabelMapping:
    def test_all_eight_raw_labels_mapped(self):
        expected_labels = {"angry", "calm", "disgust", "fearful", "happy", "neutral", "sad", "surprised"}
        assert set(RAW_LABEL_TO_CATEGORY.keys()) == expected_labels

    def test_mapping_targets_only_spec_categories(self):
        assert set(RAW_LABEL_TO_CATEGORY.values()) <= set(EmotionCategory)


class TestAggregateScores:
    def test_aggregates_into_six_categories(self):
        result = _aggregate_scores(_high_engaged_scores())
        assert set(result.keys()) == set(EmotionCategory)
        assert pytest.approx(sum(result.values()), abs=1e-6) == 1.0

    def test_engaged_dominates_when_happy_high(self):
        result = _aggregate_scores(_high_engaged_scores())
        assert max(result, key=result.get) == EmotionCategory.ENGAGED

    def test_unknown_labels_skipped(self):
        result = _aggregate_scores([{"label": "made_up", "score": 0.9}])
        assert all(v == 0.0 for v in result.values())


class TestAnalyzeSegments:
    def test_produces_one_annotation_per_segment(self, audio, segments):
        classifier = FakeClassifier([_high_engaged_scores(), _ambiguous_scores()])
        result = analyze_segments(audio_path=None, segments=segments, classifier=classifier, audio_array=audio)
        assert len(result) == 2
        assert classifier.invocations == 2

    def test_high_confidence_annotation(self, audio, segments):
        classifier = FakeClassifier([_high_engaged_scores()])
        result = analyze_segments(audio_path=None, segments=[segments[0]], classifier=classifier, audio_array=audio)
        annotation = result[0]
        assert annotation.segment_id == "s0"
        assert annotation.speaker == "SPEAKER_00"
        assert annotation.primary_emotion == EmotionCategory.ENGAGED
        # happy + surprised both map to engaged
        assert annotation.confidence == pytest.approx(0.85, abs=1e-4)
        assert annotation.low_confidence is False

    def test_low_confidence_flag_set_when_below_threshold(self, audio, segments):
        classifier = FakeClassifier([_ambiguous_scores()])
        result = analyze_segments(audio_path=None, segments=[segments[0]], classifier=classifier, audio_array=audio)
        annotation = result[0]
        assert annotation.confidence < LOW_CONFIDENCE_THRESHOLD
        assert annotation.low_confidence is True

    def test_emotion_scores_includes_all_six_categories(self, audio, segments):
        classifier = FakeClassifier([_high_engaged_scores()])
        result = analyze_segments(audio_path=None, segments=[segments[0]], classifier=classifier, audio_array=audio)
        scores = result[0].emotion_scores
        assert set(scores.keys()) == {c.value for c in EmotionCategory}

    def test_skips_segments_too_short(self, audio):
        short_segment = TranscriptSegment(id="x", start=0.0, end=0.1, speaker="SPEAKER_00", text="oh")
        classifier = FakeClassifier([])
        result = analyze_segments(audio_path=None, segments=[short_segment], classifier=classifier, audio_array=audio)
        assert result == []
        assert classifier.invocations == 0

    def test_segment_failure_does_not_abort_batch(self, audio, segments):
        class ExplodingClassifier:
            def __init__(self):
                self.calls = 0

            def __call__(self, payload, top_k=None):
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("boom")
                return _high_engaged_scores()

        result = analyze_segments(
            audio_path=None, segments=segments, classifier=ExplodingClassifier(), audio_array=audio
        )
        # First segment errored, second produced an annotation
        assert len(result) == 1
        assert result[0].segment_id == "s1"
