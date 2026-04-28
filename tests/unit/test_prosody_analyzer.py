from __future__ import annotations

from unittest.mock import patch

import pytest

pytest.importorskip("numpy")
pytest.importorskip("parselmouth")

import numpy as np

from backend.schemas import TranscriptSegment
from backend.services.prosody_analyzer import (
    NON_SPEECH_RMS_FLOOR,
    REASON_EXTRACTION_FAILED,
    REASON_NON_SPEECH,
    SAMPLE_RATE,
    _compute_pause_ratio,
    _compute_rms,
    _compute_speaking_rate,
    analyze_segments,
)


def _sine(freq_hz: float, duration_s: float, amplitude: float = 0.3, sr: int = SAMPLE_RATE) -> np.ndarray:
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False, dtype=np.float64)
    return (amplitude * np.sin(2 * np.pi * freq_hz * t)).astype(np.float64)


def _silence(duration_s: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    return np.zeros(int(sr * duration_s), dtype=np.float64)


def _segment(seg_id: str, start: float, end: float, text: str = "hello there friend", speaker: str = "SPEAKER_00"):
    return TranscriptSegment(id=seg_id, start=start, end=end, speaker=speaker, text=text)


class TestComputeRMS:
    def test_zero_for_empty(self):
        assert _compute_rms(np.array([])) == 0.0

    def test_zero_for_silence(self):
        assert _compute_rms(_silence(1.0)) == 0.0

    def test_matches_known_value_for_sine(self):
        # RMS of a unit-amplitude sine is 1/sqrt(2) ≈ 0.707
        sine = _sine(220.0, 1.0, amplitude=1.0)
        assert _compute_rms(sine) == pytest.approx(1.0 / np.sqrt(2), abs=1e-3)


class TestComputeSpeakingRate:
    def test_basic_wpm(self):
        # 6 words in 2 seconds → 180 WPM
        assert _compute_speaking_rate("one two three four five six", 2.0) == 180.0

    def test_zero_duration(self):
        assert _compute_speaking_rate("hello", 0.0) == 0.0

    def test_empty_text(self):
        assert _compute_speaking_rate("", 2.0) == 0.0


class TestComputePauseRatio:
    def test_pure_silence_is_one(self):
        assert _compute_pause_ratio(_silence(1.0), SAMPLE_RATE) == pytest.approx(1.0, abs=1e-6)

    def test_continuous_sine_has_low_pause(self):
        # A pure tone has near-constant frame RMS, so very few frames fall
        # below the relative pause threshold.
        sine = _sine(220.0, 1.0)
        assert _compute_pause_ratio(sine, SAMPLE_RATE) < 0.1

    def test_half_silence_half_speech(self):
        # 0.5s of speech, 0.5s of silence → roughly half the frames silent
        signal = np.concatenate([_sine(220.0, 0.5), _silence(0.5)])
        ratio = _compute_pause_ratio(signal, SAMPLE_RATE)
        assert 0.4 < ratio < 0.6


class TestAnalyzeSegmentsHappyPath:
    def test_extracts_pitch_close_to_input_frequency(self):
        # 2 seconds of 220 Hz sine
        audio = _sine(220.0, 2.0)
        segments = [_segment("s0", 0.0, 2.0, text="some words here being spoken aloud")]
        annotations, unavailable = analyze_segments(audio, segments)

        assert len(annotations) == 1
        assert unavailable == []
        ann = annotations[0]
        # Praat should recover ~220 Hz on a clean sine
        assert 210.0 < ann.pitch_mean < 230.0
        assert ann.pitch_variance >= 0.0
        # Volume normalized 0-1 and reasonable for a single segment
        assert 0.0 <= ann.volume_mean <= 1.0
        assert ann.volume_variance >= 0.0
        # Speaking rate: 6 words / 2s = 180 WPM
        assert ann.speaking_rate == 180.0
        # Continuous tone has very low pause ratio
        assert ann.pause_ratio < 0.2

    def test_segment_id_and_speaker_are_carried_through(self):
        audio = _sine(180.0, 1.5)
        segments = [_segment("seg-xyz", 0.0, 1.5, speaker="SPEAKER_07", text="the quick brown fox jumps")]
        annotations, _ = analyze_segments(audio, segments)
        assert annotations[0].segment_id == "seg-xyz"
        assert annotations[0].speaker == "SPEAKER_07"
        assert annotations[0].start == 0.0
        assert annotations[0].end == 1.5


class TestNonSpeechExclusion:
    def test_silence_segment_recorded_as_non_speech(self):
        audio = _silence(2.0)
        segments = [_segment("silent-0", 0.0, 2.0, text="")]
        annotations, unavailable = analyze_segments(audio, segments)
        assert annotations == []
        assert len(unavailable) == 1
        assert unavailable[0].segment_id == "silent-0"
        assert unavailable[0].reason == REASON_NON_SPEECH

    def test_speech_segment_kept_when_silence_segment_excluded(self):
        # First half: sine speech, second half: silence
        audio = np.concatenate([_sine(220.0, 1.0), _silence(1.0)])
        segments = [
            _segment("s0", 0.0, 1.0, text="alpha bravo charlie delta"),
            _segment("s1", 1.0, 2.0, text=""),
        ]
        annotations, unavailable = analyze_segments(audio, segments)
        assert len(annotations) == 1
        assert annotations[0].segment_id == "s0"
        assert len(unavailable) == 1
        assert unavailable[0].segment_id == "s1"
        assert unavailable[0].reason == REASON_NON_SPEECH


class TestVolumeNormalization:
    def test_loud_segment_normalizes_higher_than_quiet_segment(self):
        # Two segments, one at 4x the amplitude of the other
        loud = _sine(220.0, 1.0, amplitude=0.4)
        quiet = _sine(220.0, 1.0, amplitude=0.1)
        audio = np.concatenate([loud, quiet])
        segments = [
            _segment("loud", 0.0, 1.0, text="some loud words being said"),
            _segment("quiet", 1.0, 2.0, text="some quiet words being said"),
        ]
        annotations, _ = analyze_segments(audio, segments)
        by_id = {a.segment_id: a for a in annotations}
        assert by_id["loud"].volume_mean > by_id["quiet"].volume_mean
        assert 0.0 <= by_id["quiet"].volume_mean <= 1.0
        assert 0.0 <= by_id["loud"].volume_mean <= 1.0
        # Loudest segment normalizes near (but typically below) 1.0; ratio
        # should be roughly 4:1 since amplitudes are 4:1
        ratio = by_id["loud"].volume_mean / by_id["quiet"].volume_mean
        assert 3.0 < ratio < 5.0


class TestPerSegmentFailureTolerance:
    def test_one_segment_failure_does_not_abort_batch(self):
        audio = _sine(220.0, 2.0)
        segments = [
            _segment("ok", 0.0, 1.0, text="some words here"),
            _segment("boom", 1.0, 2.0, text="more words now"),
        ]

        original_extract = None
        from backend.services import prosody_analyzer as mod

        original_extract = mod._extract_segment_features

        def explode_for_boom(audio_array, segment, sampling_rate):
            if segment.id == "boom":
                raise RuntimeError("synthetic failure")
            return original_extract(audio_array, segment, sampling_rate)

        with patch.object(mod, "_extract_segment_features", side_effect=explode_for_boom):
            annotations, unavailable = analyze_segments(audio, segments)

        assert len(annotations) == 1
        assert annotations[0].segment_id == "ok"
        assert len(unavailable) == 1
        assert unavailable[0].segment_id == "boom"
        assert unavailable[0].reason == REASON_EXTRACTION_FAILED


class TestShortSegmentsSkipped:
    def test_segment_below_min_duration_skipped(self):
        audio = _sine(220.0, 2.0)
        segments = [_segment("tiny", 0.0, 0.1, text="hi")]
        annotations, unavailable = analyze_segments(audio, segments)
        # Below MIN_SEGMENT_SECONDS the analyzer skips silently — neither
        # produces an annotation nor an unavailable marker.
        assert annotations == []
        assert unavailable == []


class TestNonSpeechFloor:
    def test_floor_is_meaningfully_low(self):
        # Sanity check: the floor needs to admit normal speech RMS levels
        sine = _sine(220.0, 1.0, amplitude=0.05)
        assert _compute_rms(sine) > NON_SPEECH_RMS_FLOOR
