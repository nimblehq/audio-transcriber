from __future__ import annotations

import pytest

from backend.schemas import (
    AudioAnalysis,
    AudioAnalysisStatus,
    EmotionAnnotation,
    EmotionCategory,
    InteractionEvent,
    InteractionEventType,
    SegmentInteraction,
    Transcript,
    TranscriptSegment,
)
from backend.services import analysis_context


def _emotion(
    *,
    segment_id: str = "seg_0",
    speaker: str = "SPEAKER_00",
    start: float = 0.0,
    end: float = 1.0,
    primary: EmotionCategory = EmotionCategory.NEUTRAL,
    confidence: float = 0.9,
) -> EmotionAnnotation:
    return EmotionAnnotation(
        segment_id=segment_id,
        speaker=speaker,
        start=start,
        end=end,
        primary_emotion=primary,
        confidence=confidence,
        emotion_scores={primary.value: confidence},
        low_confidence=confidence < 0.5,
    )


def _segment(
    *,
    seg_id: str = "seg_0",
    speaker: str = "SPEAKER_00",
    start: float = 0.0,
    end: float = 1.0,
    text: str = "hello",
) -> TranscriptSegment:
    return TranscriptSegment(id=seg_id, start=start, end=end, speaker=speaker, text=text)


def _completed_audio_analysis(**kwargs) -> AudioAnalysis:
    defaults = {
        "status": AudioAnalysisStatus.COMPLETED,
        "emotion_status": AudioAnalysisStatus.COMPLETED,
        "prosody_status": AudioAnalysisStatus.COMPLETED,
        "interaction_status": AudioAnalysisStatus.COMPLETED,
    }
    defaults.update(kwargs)
    return AudioAnalysis(**defaults)


class TestRenderOptOut:
    def test_returns_empty_string_when_audio_analysis_is_none(self):
        assert analysis_context.render(None, transcript=None) == ""


class TestRenderUnavailable:
    def test_failed_status_returns_brief_unavailability_note(self):
        aa = AudioAnalysis(status=AudioAnalysisStatus.FAILED, reason="model_load_error")
        out = analysis_context.render(aa, transcript=None)
        assert out.startswith("## Audio Analysis Context")
        assert "unavailable" in out
        assert "model_load_error" in out
        assert "### Emotional Patterns" not in out

    def test_unavailable_status_returns_brief_note(self):
        aa = AudioAnalysis(status=AudioAnalysisStatus.UNAVAILABLE, reason="language_not_supported:fr")
        out = analysis_context.render(aa, transcript=None)
        assert "unavailable" in out
        assert "language_not_supported:fr" in out

    def test_failed_status_without_reason_uses_default(self):
        aa = AudioAnalysis(status=AudioAnalysisStatus.FAILED)
        out = analysis_context.render(aa, transcript=None)
        assert "audio analysis was not produced" in out


class TestEmotionalPatterns:
    def test_predominant_emotion_with_percentage(self):
        emotions = [
            _emotion(segment_id="s1", primary=EmotionCategory.ENGAGED, confidence=0.9),
            _emotion(segment_id="s2", primary=EmotionCategory.ENGAGED, confidence=0.8),
            _emotion(segment_id="s3", primary=EmotionCategory.NEUTRAL, confidence=0.7),
        ]
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=None)
        assert "predominantly engaged (67%)" in out

    def test_uses_speaker_display_name(self):
        emotions = [_emotion(speaker="SPEAKER_00", primary=EmotionCategory.NEUTRAL)]
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=None, speakers={"SPEAKER_00": "Alice"})
        assert "Alice" in out
        assert "SPEAKER_00" not in out

    def test_surfaces_high_confidence_negative_spikes(self):
        emotions = [
            _emotion(segment_id="s1", start=10.0, primary=EmotionCategory.ENGAGED, confidence=0.9),
            _emotion(segment_id="s2", start=754.0, primary=EmotionCategory.FRUSTRATED, confidence=0.95),
        ]
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=None)
        assert "frustrated at 12:34" in out

    def test_does_not_surface_low_confidence_spikes(self):
        emotions = [
            _emotion(segment_id="s1", primary=EmotionCategory.ENGAGED, confidence=0.9),
            _emotion(segment_id="s2", start=60.0, primary=EmotionCategory.FRUSTRATED, confidence=0.4),
        ]
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=None)
        assert "spikes" not in out


class TestWordToneMismatches:
    def test_detects_agreement_phrase_with_frustrated_tone(self):
        emotions = [
            _emotion(
                segment_id="s1",
                speaker="SPEAKER_00",
                start=15.23,
                primary=EmotionCategory.FRUSTRATED,
                confidence=0.78,
            )
        ]
        transcript = Transcript(
            segments=[_segment(seg_id="s1", speaker="SPEAKER_00", start=15.23, text="That works for me.")]
        )
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=transcript)
        assert "### Word-Tone Mismatches" in out
        assert "tone indicates frustrated" in out
        assert "0.78" in out
        assert "That works for me." in out

    def test_hedges_low_confidence_mismatch(self):
        emotions = [
            _emotion(
                segment_id="s1",
                primary=EmotionCategory.UNCERTAIN,
                confidence=0.42,
            )
        ]
        transcript = Transcript(segments=[_segment(seg_id="s1", text="No concerns here.")])
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=transcript)
        assert "tone may indicate uncertain" in out
        assert "tone indicates" not in out

    def test_no_mismatch_when_text_does_not_signal_agreement(self):
        emotions = [_emotion(segment_id="s1", primary=EmotionCategory.FRUSTRATED, confidence=0.9)]
        transcript = Transcript(segments=[_segment(seg_id="s1", text="The deadline is impossible.")])
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=transcript)
        assert "### Word-Tone Mismatches" not in out

    def test_no_mismatch_when_emotion_is_neutral(self):
        emotions = [_emotion(segment_id="s1", primary=EmotionCategory.NEUTRAL, confidence=0.9)]
        transcript = Transcript(segments=[_segment(seg_id="s1", text="That works for me.")])
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=transcript)
        assert "### Word-Tone Mismatches" not in out


class TestInteractionDynamics:
    def test_counts_interruptions_per_pair(self):
        events = [
            InteractionEvent(
                event_type=InteractionEventType.INTERRUPTION,
                timestamp=10.0,
                speaker_a="SPEAKER_01",
                speaker_b="SPEAKER_00",
                duration=0.4,
            ),
            InteractionEvent(
                event_type=InteractionEventType.INTERRUPTION,
                timestamp=22.0,
                speaker_a="SPEAKER_01",
                speaker_b="SPEAKER_00",
                duration=0.5,
            ),
        ]
        aa = _completed_audio_analysis(interactions=events)
        out = analysis_context.render(aa, transcript=None)
        assert "### Interaction Dynamics" in out
        assert "SPEAKER_00 interrupted SPEAKER_01 2 times (reverse: 0)" in out

    def test_emits_average_response_latency_per_speaker(self):
        segment_interactions = [
            SegmentInteraction(segment_id="s1", hesitation_before=0.4),
            SegmentInteraction(segment_id="s2", hesitation_before=2.0),
        ]
        transcript = Transcript(
            segments=[
                _segment(seg_id="s1", speaker="SPEAKER_00"),
                _segment(seg_id="s2", speaker="SPEAKER_01"),
            ]
        )
        aa = _completed_audio_analysis(segment_interactions=segment_interactions)
        out = analysis_context.render(aa, transcript=transcript)
        assert "Average response latency:" in out
        assert "SPEAKER_00 (0.4s)" in out
        assert "SPEAKER_01 (2.0s)" in out

    def test_dominant_speaker_limitation_appends_disclosure(self):
        emotions = [_emotion(primary=EmotionCategory.ENGAGED)]
        aa = _completed_audio_analysis(emotions=emotions, dominant_speaker_limitation=True)
        out = analysis_context.render(aa, transcript=None)
        assert "single speaker dominates" in out

    def test_dominance_alone_renders_interaction_section(self):
        # No interactions but the limitation flag is set — section should still appear.
        aa = _completed_audio_analysis(dominant_speaker_limitation=True)
        out = analysis_context.render(aa, transcript=None)
        assert "### Interaction Dynamics" in out
        assert "single speaker dominates" in out


class TestEnergyTrajectory:
    def test_reports_peak_and_trough_windows(self):
        emotions = [
            _emotion(segment_id="s1", start=30.0, end=60.0, primary=EmotionCategory.ENGAGED, confidence=0.9),
            _emotion(
                segment_id="s2",
                start=2200.0,
                end=2230.0,
                primary=EmotionCategory.DISENGAGED,
                confidence=0.85,
            ),
        ]
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=None)
        assert "### Energy Trajectory" in out
        assert "peaked" in out
        assert "lowest" in out

    def test_single_window_does_not_emit_separate_trough(self):
        emotions = [_emotion(segment_id="s1", start=10.0, primary=EmotionCategory.ENGAGED, confidence=0.9)]
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=None)
        assert "peaked" in out
        assert "lowest" not in out


class TestInstructions:
    def test_completed_render_includes_audio_analysis_instructions(self):
        emotions = [_emotion(primary=EmotionCategory.NEUTRAL, confidence=0.9)]
        aa = _completed_audio_analysis(emotions=emotions)
        out = analysis_context.render(aa, transcript=None)
        assert "## Audio Analysis Instructions" in out
        assert "Hidden disagreements" in out
        assert "Contribution quality" in out
        assert "Psychological safety" in out
        assert "Meeting effectiveness" in out

    def test_unavailable_render_omits_instructions(self):
        aa = AudioAnalysis(status=AudioAnalysisStatus.FAILED, reason="oops")
        out = analysis_context.render(aa, transcript=None)
        assert "## Audio Analysis Instructions" not in out

    def test_completed_with_no_data_falls_back_to_unavailability(self):
        # COMPLETED status but every list is empty — there is nothing to surface.
        aa = _completed_audio_analysis()
        out = analysis_context.render(aa, transcript=None)
        assert "unavailable" in out
        assert "## Audio Analysis Instructions" not in out


@pytest.mark.parametrize(
    "phrase",
    [
        "That works for me.",
        "Yeah, sounds good.",
        "No concerns here.",
        "Agreed.",
        "I'm fine with that.",
        "Looks good.",
    ],
)
def test_agreement_phrase_lexicon_matches_common_acceptance_language(phrase):
    emotions = [_emotion(segment_id="s1", primary=EmotionCategory.FRUSTRATED, confidence=0.8)]
    transcript = Transcript(segments=[_segment(seg_id="s1", text=phrase)])
    aa = _completed_audio_analysis(emotions=emotions)
    out = analysis_context.render(aa, transcript=transcript)
    assert "### Word-Tone Mismatches" in out
