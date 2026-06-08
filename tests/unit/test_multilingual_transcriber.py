from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend.services.multilingual_transcriber import (
    LANG_MIN_CHUNK_SEC,
    SAMPLE_RATE,
    _classify_chunk,
    _constrained_language,
    _dominant_language,
    _vad_chunks,
    transcribe_multilingual,
)


class _FakeSegment:
    """Stand-in for a faster-whisper Segment."""

    def __init__(self, start: float, end: float, text: str):
        self.start = start
        self.end = end
        self.text = text


class TestConstrainedLanguage:
    def test_picks_most_probable_within_set(self):
        probs = [("en", 0.6), ("th", 0.3), ("fr", 0.09)]
        lang, conf, raw = _constrained_language(probs, {"en", "th"})
        assert lang == "en"
        assert raw == 0.6

    def test_never_returns_unselected_language(self):
        # French is most probable overall but not selected — must never be chosen.
        probs = [("fr", 0.8), ("th", 0.15), ("en", 0.05)]
        lang, _, _ = _constrained_language(probs, {"en", "th"})
        assert lang in {"en", "th"}
        assert lang == "th"

    def test_confidence_renormalized_within_set(self):
        # Within {en, th}: en=0.2, th=0.1 → renormalized en confidence = 0.2/0.3.
        probs = {"fr": 0.7, "en": 0.2, "th": 0.1}
        lang, conf, raw = _constrained_language(probs, {"en", "th"})
        assert lang == "en"
        assert raw == 0.2
        assert abs(conf - (0.2 / 0.3)) < 1e-9

    def test_missing_codes_treated_as_zero(self):
        lang, conf, raw = _constrained_language({"en": 0.9}, {"en", "th"})
        assert lang == "en"
        assert raw == 0.9

    def test_tie_breaks_deterministically(self):
        lang, _, _ = _constrained_language({"en": 0.5, "th": 0.5}, {"en", "th"})
        assert lang == "en"  # alphabetical


class TestClassifyChunk:
    def test_short_chunk_returns_none(self):
        probs = [("en", 0.99)]
        assert _classify_chunk(probs, {"en", "th"}, duration=LANG_MIN_CHUNK_SEC - 0.1) is None

    def test_confident_long_chunk_classified(self):
        probs = [("en", 0.95), ("th", 0.05)]
        assert _classify_chunk(probs, {"en", "th"}, duration=5.0) == "en"

    def test_ambiguous_chunk_returns_none(self):
        # 0.52 / 0.48 within set → below the 0.70 confidence threshold.
        probs = {"en": 0.52, "th": 0.48}
        assert _classify_chunk(probs, {"en", "th"}, duration=5.0) is None

    def test_low_raw_probability_returns_none(self):
        # Renormalized confidence is high, but raw prob is below the floor
        # (mostly silence/noise: neither selected language scores well).
        probs = {"en": 0.2, "th": 0.01, "fr": 0.0}
        assert _classify_chunk(probs, {"en", "th"}, duration=5.0) is None


class TestDominantLanguage:
    def test_duration_weighted(self):
        classified = [("en", 2.0), ("th", 5.0), ("en", 1.0)]
        assert _dominant_language(classified, {"en", "th"}) == "th"

    def test_ignores_unclassified_chunks(self):
        classified = [("en", 2.0), (None, 100.0)]
        assert _dominant_language(classified, {"en", "th"}) == "en"

    def test_empty_falls_back_to_deterministic_pick(self):
        classified = [(None, 3.0), (None, 1.0)]
        assert _dominant_language(classified, {"th", "en"}) == "en"  # sorted → first

    def test_weight_tie_breaks_deterministically(self):
        classified = [("th", 2.0), ("en", 2.0)]
        assert _dominant_language(classified, {"en", "th"}) == "en"


def _build_pipeline(detect_results, transcribe_results):
    """Build a fake whisperx pipeline whose model returns scripted detect/transcribe values.

    detect_results: list of all_language_probs (one per chunk, in order).
    transcribe_results: list of lists of _FakeSegment (one per chunk, in order).
    """
    model = MagicMock()
    model.detect_language.side_effect = [("xx", 0.0, probs) for probs in detect_results]
    model.transcribe.side_effect = [(segs, None) for segs in transcribe_results]
    pipeline = MagicMock()
    pipeline.model = model
    return pipeline


class TestTranscribeMultilingual:
    def _audio(self, seconds: float):
        # A plain Python list so slicing/len work without numpy (absent in CI).
        return [0.1] * int(SAMPLE_RATE * seconds)

    def test_each_chunk_tagged_with_detected_language(self):
        chunks = [{"start": 0.0, "end": 3.0}, {"start": 3.0, "end": 6.0}]
        pipeline = _build_pipeline(
            detect_results=[[("en", 0.95), ("th", 0.05)], [("th", 0.95), ("en", 0.05)]],
            transcribe_results=[[_FakeSegment(0.0, 1.0, "Hello")], [_FakeSegment(0.0, 1.0, "สวัสดี")]],
        )
        with patch("backend.services.multilingual_transcriber._vad_chunks", return_value=chunks):
            segments, dominant = transcribe_multilingual(self._audio(6), {"en", "th"}, pipeline)

        assert [s["language"] for s in segments] == ["en", "th"]
        assert [s["text"] for s in segments] == ["Hello", "สวัสดี"]
        # Each chunk transcribed in its own detected language.
        assert pipeline.model.transcribe.call_args_list[0].kwargs["language"] == "en"
        assert pipeline.model.transcribe.call_args_list[1].kwargs["language"] == "th"

    def test_timestamps_offset_to_absolute_time(self):
        chunks = [{"start": 10.0, "end": 13.0}]
        pipeline = _build_pipeline(
            detect_results=[[("en", 0.99)]],
            transcribe_results=[[_FakeSegment(0.5, 2.0, "Hi")]],
        )
        with patch("backend.services.multilingual_transcriber._vad_chunks", return_value=chunks):
            segments, _ = transcribe_multilingual(self._audio(13), {"en", "th"}, pipeline)

        assert segments[0]["start"] == 10.5
        assert segments[0]["end"] == 12.0

    def test_short_chunk_falls_back_to_dominant(self):
        # Chunk 0: long English. Chunk 1: too short to classify → dominant (en).
        chunks = [{"start": 0.0, "end": 5.0}, {"start": 5.0, "end": 5.5}]
        pipeline = _build_pipeline(
            detect_results=[[("en", 0.99), ("th", 0.01)]],  # only the long chunk is detected
            transcribe_results=[[_FakeSegment(0.0, 4.0, "Long english")], [_FakeSegment(0.0, 0.4, "ok")]],
        )
        with patch("backend.services.multilingual_transcriber._vad_chunks", return_value=chunks):
            segments, dominant = transcribe_multilingual(self._audio(6), {"en", "th"}, pipeline)

        assert dominant == "en"
        # Short chunk was not sent to detect_language (duration gate), got dominant.
        assert pipeline.model.detect_language.call_count == 1
        assert segments[1]["language"] == "en"
        assert pipeline.model.transcribe.call_args_list[1].kwargs["language"] == "en"

    def test_ambiguous_chunk_falls_back_to_dominant(self):
        chunks = [{"start": 0.0, "end": 6.0}, {"start": 6.0, "end": 12.0}]
        pipeline = _build_pipeline(
            detect_results=[
                [("th", 0.95), ("en", 0.05)],  # chunk 0: clearly Thai
                [("en", 0.51), ("th", 0.49)],  # chunk 1: ambiguous → dominant (th)
            ],
            transcribe_results=[[_FakeSegment(0.0, 5.0, "ไทย")], [_FakeSegment(0.0, 5.0, "????")]],
        )
        with patch("backend.services.multilingual_transcriber._vad_chunks", return_value=chunks):
            segments, dominant = transcribe_multilingual(self._audio(12), {"en", "th"}, pipeline)

        assert dominant == "th"
        assert segments[1]["language"] == "th"

    def test_empty_text_segments_dropped(self):
        chunks = [{"start": 0.0, "end": 3.0}]
        pipeline = _build_pipeline(
            detect_results=[[("en", 0.99)]],
            transcribe_results=[[_FakeSegment(0.0, 1.0, "  "), _FakeSegment(1.0, 2.0, "Real")]],
        )
        with patch("backend.services.multilingual_transcriber._vad_chunks", return_value=chunks):
            segments, _ = transcribe_multilingual(self._audio(3), {"en", "th"}, pipeline)

        assert [s["text"] for s in segments] == ["Real"]

    def test_no_chunks_returns_empty_with_deterministic_language(self):
        pipeline = _build_pipeline(detect_results=[], transcribe_results=[])
        with patch("backend.services.multilingual_transcriber._vad_chunks", return_value=[]):
            segments, dominant = transcribe_multilingual(self._audio(1), {"th", "en"}, pipeline)
        assert segments == []
        assert dominant == "en"

    def test_detection_failure_falls_back_to_dominant(self):
        chunks = [{"start": 0.0, "end": 5.0}, {"start": 5.0, "end": 10.0}]
        model = MagicMock()
        # First chunk detection raises; second succeeds as English.
        model.detect_language.side_effect = [RuntimeError("boom"), ("en", 0.9, [("en", 0.99)])]
        model.transcribe.side_effect = [
            ([_FakeSegment(0.0, 4.0, "a")], None),
            ([_FakeSegment(0.0, 4.0, "b")], None),
        ]
        pipeline = MagicMock()
        pipeline.model = model
        with patch("backend.services.multilingual_transcriber._vad_chunks", return_value=chunks):
            segments, dominant = transcribe_multilingual(self._audio(10), {"en", "th"}, pipeline)
        assert dominant == "en"
        assert all(s["language"] == "en" for s in segments)

    def test_progress_callback_invoked(self):
        chunks = [{"start": 0.0, "end": 3.0}]
        pipeline = _build_pipeline(
            detect_results=[[("en", 0.99)]],
            transcribe_results=[[_FakeSegment(0.0, 1.0, "Hi")]],
        )
        cb = MagicMock()
        with patch("backend.services.multilingual_transcriber._vad_chunks", return_value=chunks):
            transcribe_multilingual(self._audio(3), {"en", "th"}, pipeline, progress_cb=cb)
        assert cb.call_count >= 2  # at least the pass markers


class TestVadChunks:
    def test_reproduces_whisperx_vad_merge(self):
        class _Vad:  # stand-in for whisperx.vads.vad.Vad
            pass

        class _FakeVadModel(_Vad):
            def __init__(self):
                self.preprocess_audio = MagicMock(return_value="waveform")
                self.merge_chunks = MagicMock(return_value=[{"start": 0.0, "end": 2.5}, {"start": 2.5, "end": 4.0}])

            def __call__(self, _payload):
                return "raw_segments"

        vad_model = _FakeVadModel()
        pipeline = MagicMock()
        pipeline.vad_model = vad_model
        pipeline._vad_params = {"chunk_size": 30, "vad_onset": 0.5, "vad_offset": 0.363}

        fake_vad_module = MagicMock()
        fake_vad_module.Vad = _Vad
        with patch.dict("sys.modules", {"whisperx.vads.vad": fake_vad_module}):
            chunks = _vad_chunks([0.0] * 100, pipeline)

        vad_model.preprocess_audio.assert_called_once()
        # merge_chunks called with the pipeline's VAD params.
        assert vad_model.merge_chunks.call_args.kwargs == {"chunk_size": 30, "onset": 0.5, "offset": 0.363}
        assert chunks == [{"start": 0.0, "end": 2.5}, {"start": 2.5, "end": 4.0}]
