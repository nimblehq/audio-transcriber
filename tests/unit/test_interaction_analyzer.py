from __future__ import annotations

from backend.schemas import InteractionEventType, TranscriptSegment
from backend.services.interaction_analyzer import (
    BACKCHANNEL_MAX_DURATION,
    BACKCHANNEL_SHORT_DURATION,
    DOMINANT_SPEAKER_THRESHOLD,
    HESITATION_MIN_SECONDS,
    LONG_PAUSE_MIN_SECONDS,
    _is_backchannel,
    _is_backchannel_text,
    analyze,
)


def _seg(
    seg_id: str, start: float, end: float, speaker: str = "SPEAKER_00", text: str = "hello world"
) -> TranscriptSegment:
    return TranscriptSegment(id=seg_id, start=start, end=end, speaker=speaker, text=text)


class TestBackchannelTextHeuristic:
    def test_pure_acknowledgement_is_backchannel(self):
        assert _is_backchannel_text("yeah") is True
        assert _is_backchannel_text("Mm-hmm") is True
        assert _is_backchannel_text("uh-huh.") is True
        assert _is_backchannel_text("right!") is True

    def test_short_phrase_with_acknowledgement_is_backchannel(self):
        assert _is_backchannel_text("yeah ok") is True
        assert _is_backchannel_text("got it") is True

    def test_long_agreement_statement_is_not_backchannel(self):
        assert _is_backchannel_text("yeah I think we should review the entire budget") is False

    def test_substantive_content_is_not_backchannel(self):
        assert _is_backchannel_text("Tuesday") is False
        assert _is_backchannel_text("That's a hard problem to solve") is False

    def test_empty_text_is_not_backchannel(self):
        assert _is_backchannel_text("") is False
        assert _is_backchannel_text("   ") is False

    def test_expanded_token_set_covers_common_acknowledgements(self):
        # Production logs surfaced these escaping the original token list
        for token in ["Nice.", "cool", "Great!", "perfect", "Awesome.", "makes sense", "fair enough", "agreed"]:
            assert _is_backchannel_text(token) is True, f"{token!r} should be a back-channel"


class TestBackchannelCombinedHeuristic:
    """The combined check (duration cap + lexicon, OR sub-second + ≤2 words)."""

    def test_short_lexical_match_is_backchannel(self):
        assert _is_backchannel(0.4, "yeah") is True
        assert _is_backchannel(1.2, "got it") is True

    def test_long_lexical_match_is_not_backchannel(self):
        # Above duration cap, lexical match alone isn't enough
        assert _is_backchannel(BACKCHANNEL_MAX_DURATION + 0.1, "yeah") is False

    def test_sub_second_unknown_word_is_backchannel_via_duration_floor(self):
        # "Nice." escapes the original lexicon but is still clearly a back-channel
        # at 0.13s. The duration floor catches it.
        assert _is_backchannel(0.13, "Nice.") is True
        assert _is_backchannel(BACKCHANNEL_SHORT_DURATION, "huh?") is True

    def test_sub_second_long_phrase_is_not_backchannel(self):
        # Even at sub-second, more than 2 words shouldn't trigger the floor
        assert _is_backchannel(0.4, "the budget plan now") is False

    def test_above_short_duration_unknown_word_is_not_backchannel(self):
        # "Tuesday" at 0.8s — neither lexical nor under the short-duration floor
        assert _is_backchannel(0.8, "Tuesday") is False

    def test_sub_floor_with_no_text_is_backchannel(self):
        # A sub-0.5s PyAnnote turn that WhisperX didn't transcribe — almost
        # always a brief vocalization or breath, not a real interruption.
        assert _is_backchannel(0.2, "") is True
        assert _is_backchannel(0.4, "   ") is True

    def test_above_short_duration_with_no_text_is_not_backchannel(self):
        # A 1s+ turn with no transcript shouldn't be auto-classified as
        # back-channel — could be inaudible substantive speech
        assert _is_backchannel(1.2, "") is False


class TestInterruptionDetection:
    """AC1, AC2, AC3, BR-3.1 — overlapping turns produce interruption events
    unless the interrupter's utterance is a back-channel."""

    def test_overlap_with_substantive_content_is_interruption(self):
        # A speaks 0-5, B starts at 3 and continues to 6 with substantive content
        diarize_turns = [(0.0, 5.0, "A"), (3.0, 6.0, "B")]
        segments = [
            _seg("a0", 0.0, 5.0, speaker="A", text="we should review the entire budget plan"),
            _seg("b0", 3.0, 6.0, speaker="B", text="actually I disagree with that approach"),
        ]
        result = analyze(segments, diarize_turns)
        interruptions = [e for e in result.events if e.event_type == InteractionEventType.INTERRUPTION]
        assert len(interruptions) == 1
        ev = interruptions[0]
        assert ev.speaker_a == "A"
        assert ev.speaker_b == "B"
        assert ev.timestamp == 3.0
        assert ev.duration == 2.0
        assert "actually" in ev.context.lower()

    def test_backchannel_overlap_is_classified_as_overlap_not_interruption(self):
        # A speaks 0-10, B drops a 0.5s "yeah" at 4.0
        diarize_turns = [(0.0, 10.0, "A"), (4.0, 4.5, "B")]
        segments = [
            _seg("a0", 0.0, 10.0, speaker="A", text="and the timeline says we should ship by friday"),
            _seg("b0", 4.0, 4.5, speaker="B", text="yeah"),
        ]
        result = analyze(segments, diarize_turns)
        interruptions = [e for e in result.events if e.event_type == InteractionEventType.INTERRUPTION]
        overlaps = [e for e in result.events if e.event_type == InteractionEventType.OVERLAP]
        assert len(interruptions) == 0
        assert len(overlaps) == 1
        assert overlaps[0].speaker_b == "B"

    def test_brief_blip_with_no_transcript_is_overlap_not_interruption(self):
        # Reproduces a production case: PyAnnote detected a 0.2s crossover by
        # speaker B at t=4.0 but WhisperX didn't transcribe it. Speaker B's
        # nearest transcript segment is 200s away with substantive content.
        # Strict lookup must not pull that far-away text into the decision.
        diarize_turns = [(0.0, 10.0, "A"), (4.0, 4.2, "B")]
        segments = [
            _seg("a0", 0.0, 10.0, speaker="A", text="and we should ship by friday for the launch"),
            # B's only transcript segment is far away with substantive content
            _seg("b0", 200.0, 210.0, speaker="B", text="actually the entire approach needs revisiting"),
        ]
        result = analyze(segments, diarize_turns)
        interruptions = [e for e in result.events if e.event_type == InteractionEventType.INTERRUPTION]
        overlaps = [e for e in result.events if e.event_type == InteractionEventType.OVERLAP]
        assert len(interruptions) == 0
        assert len(overlaps) == 1
        # Lenient context should still surface something — better than empty
        assert overlaps[0].context != ""

    def test_sub_second_unknown_word_is_overlap_not_interruption(self):
        # Reproduces a production case: a 0.13s "Nice." was being classified as
        # interruption because the token wasn't in the lexicon. The duration
        # floor now catches it.
        diarize_turns = [(0.0, 10.0, "A"), (4.0, 4.13, "B")]
        segments = [
            _seg("a0", 0.0, 10.0, speaker="A", text="and the timeline says we should ship by friday"),
            _seg("b0", 4.0, 4.13, speaker="B", text="Nice."),
        ]
        result = analyze(segments, diarize_turns)
        interruptions = [e for e in result.events if e.event_type == InteractionEventType.INTERRUPTION]
        overlaps = [e for e in result.events if e.event_type == InteractionEventType.OVERLAP]
        assert len(interruptions) == 0
        assert len(overlaps) == 1

    def test_long_backchannel_phrase_is_still_interruption(self):
        # If the back-channel turn exceeds duration cap, treat as interruption
        diarize_turns = [(0.0, 10.0, "A"), (4.0, 4.0 + BACKCHANNEL_MAX_DURATION + 0.5, "B")]
        segments = [
            _seg("a0", 0.0, 10.0, speaker="A", text="we need to align on this"),
            _seg("b0", 4.0, 4.0 + BACKCHANNEL_MAX_DURATION + 0.5, speaker="B", text="yeah"),
        ]
        result = analyze(segments, diarize_turns)
        interruptions = [e for e in result.events if e.event_type == InteractionEventType.INTERRUPTION]
        assert len(interruptions) == 1

    def test_same_speaker_overlap_is_ignored(self):
        # Adjacent turns by the same speaker — even with overlap — are not events
        diarize_turns = [(0.0, 5.0, "A"), (4.0, 7.0, "A")]
        segments = [_seg("a0", 0.0, 7.0, speaker="A", text="continuing thought across two turns")]
        result = analyze(segments, diarize_turns)
        assert result.events == []


class TestPauseDetection:
    """AC4, AC2 — gaps between turns produce hesitation/long_pause events."""

    def test_short_gap_emits_no_event(self):
        # 0.3s gap — below hesitation threshold
        diarize_turns = [(0.0, 1.0, "A"), (1.3, 2.0, "B")]
        segments = [
            _seg("a0", 0.0, 1.0, speaker="A", text="any thoughts"),
            _seg("b0", 1.3, 2.0, speaker="B", text="not really"),
        ]
        result = analyze(segments, diarize_turns)
        events = [
            e
            for e in result.events
            if e.event_type in {InteractionEventType.HESITATION, InteractionEventType.LONG_PAUSE}
        ]
        assert events == []

    def test_medium_gap_emits_hesitation_event(self):
        gap = HESITATION_MIN_SECONDS + 0.2
        diarize_turns = [(0.0, 1.0, "A"), (1.0 + gap, 2.0 + gap, "B")]
        segments = [
            _seg("a0", 0.0, 1.0, speaker="A", text="how do you feel about it"),
            _seg("b0", 1.0 + gap, 2.0 + gap, speaker="B", text="i'm not sure"),
        ]
        result = analyze(segments, diarize_turns)
        hesitations = [e for e in result.events if e.event_type == InteractionEventType.HESITATION]
        assert len(hesitations) == 1
        assert hesitations[0].speaker_a == "A"
        assert hesitations[0].speaker_b == "B"
        assert hesitations[0].duration == round(gap, 2)

    def test_large_gap_emits_long_pause_event(self):
        gap = LONG_PAUSE_MIN_SECONDS + 0.5
        diarize_turns = [(0.0, 1.0, "A"), (1.0 + gap, 2.0 + gap, "B")]
        segments = [
            _seg("a0", 0.0, 1.0, speaker="A", text="any objections"),
            _seg("b0", 1.0 + gap, 2.0 + gap, speaker="B", text="well"),
        ]
        result = analyze(segments, diarize_turns)
        long_pauses = [e for e in result.events if e.event_type == InteractionEventType.LONG_PAUSE]
        assert len(long_pauses) == 1
        assert long_pauses[0].duration == round(gap, 2)

    def test_same_speaker_gap_is_ignored(self):
        diarize_turns = [(0.0, 1.0, "A"), (5.0, 6.0, "A")]
        segments = [_seg("a0", 0.0, 6.0, speaker="A", text="thinking")]
        result = analyze(segments, diarize_turns)
        assert result.events == []


class TestSegmentInteractions:
    """AC4, AC6, BR-3.3 — per-segment annotations."""

    def test_hesitation_before_recorded_for_each_segment(self):
        diarize_turns = [(0.0, 1.0, "A"), (2.5, 3.5, "B")]
        segments = [
            _seg("a0", 0.0, 1.0, speaker="A", text="ready"),
            _seg("b0", 2.5, 3.5, speaker="B", text="yes"),
        ]
        result = analyze(segments, diarize_turns)
        by_id = {s.segment_id: s for s in result.segment_interactions}
        assert by_id["a0"].hesitation_before == 0.0
        assert by_id["b0"].hesitation_before == 1.5

    def test_interruption_marks_both_sides(self):
        diarize_turns = [(0.0, 5.0, "A"), (3.0, 6.0, "B")]
        segments = [
            _seg("a0", 0.0, 5.0, speaker="A", text="i think we should do it this way"),
            _seg("b0", 3.0, 6.0, speaker="B", text="hold on let me push back on that"),
        ]
        result = analyze(segments, diarize_turns)
        by_id = {s.segment_id: s for s in result.segment_interactions}
        assert by_id["b0"].preceded_by_interruption is True
        assert by_id["a0"].followed_by_interruption is True

    def test_backchannel_does_not_set_interruption_flags(self):
        diarize_turns = [(0.0, 10.0, "A"), (4.0, 4.5, "B")]
        segments = [
            _seg("a0", 0.0, 10.0, speaker="A", text="and that's why we should proceed"),
            _seg("b0", 4.0, 4.5, speaker="B", text="yeah"),
        ]
        result = analyze(segments, diarize_turns)
        by_id = {s.segment_id: s for s in result.segment_interactions}
        assert by_id["a0"].followed_by_interruption is False
        assert by_id["b0"].preceded_by_interruption is False

    def test_every_segment_has_annotation(self):
        diarize_turns = [(0.0, 1.0, "A"), (1.5, 2.5, "B"), (3.0, 4.0, "A")]
        segments = [
            _seg("a0", 0.0, 1.0, speaker="A", text="one"),
            _seg("b0", 1.5, 2.5, speaker="B", text="two"),
            _seg("a1", 3.0, 4.0, speaker="A", text="three"),
        ]
        result = analyze(segments, diarize_turns)
        ids = {s.segment_id for s in result.segment_interactions}
        assert ids == {"a0", "b0", "a1"}


class TestDominantSpeakerLimitation:
    """AC5, BR-3.4 — single-speaker dominance is flagged but stage completes."""

    def test_dominant_speaker_above_threshold_sets_flag(self):
        # A speaks 9s, B speaks 1s → A holds 90% > 80%
        diarize_turns = [(0.0, 9.0, "A"), (9.0, 10.0, "B")]
        segments = [
            _seg("a0", 0.0, 9.0, speaker="A", text="long monologue from A"),
            _seg("b0", 9.0, 10.0, speaker="B", text="ok"),
        ]
        result = analyze(segments, diarize_turns)
        assert result.dominant_speaker_limitation is True

    def test_balanced_speakers_does_not_set_flag(self):
        diarize_turns = [(0.0, 5.0, "A"), (5.0, 10.0, "B")]
        segments = [
            _seg("a0", 0.0, 5.0, speaker="A", text="balanced share"),
            _seg("b0", 5.0, 10.0, speaker="B", text="balanced share"),
        ]
        result = analyze(segments, diarize_turns)
        assert result.dominant_speaker_limitation is False

    def test_threshold_constant_matches_spec(self):
        assert DOMINANT_SPEAKER_THRESHOLD == 0.8

    def test_dominant_meeting_still_completes_with_events(self):
        # Even when dominance is flagged, the analyzer returns events normally
        diarize_turns = [(0.0, 9.0, "A"), (4.0, 4.6, "B"), (9.0, 10.0, "B")]
        segments = [
            _seg("a0", 0.0, 9.0, speaker="A", text="a long monologue from speaker A"),
            _seg("b0", 4.0, 4.6, speaker="B", text="yeah"),
            _seg("b1", 9.0, 10.0, speaker="B", text="ok"),
        ]
        result = analyze(segments, diarize_turns)
        assert result.dominant_speaker_limitation is True
        # Back-channel still classified correctly (overlap, not interruption)
        overlap_events = [e for e in result.events if e.event_type == InteractionEventType.OVERLAP]
        assert len(overlap_events) == 1


class TestEmptyInputs:
    def test_empty_diarize_turns_returns_empty_result(self):
        result = analyze([], [])
        assert result.events == []
        assert result.segment_interactions == []
        assert result.dominant_speaker_limitation is False

    def test_segments_without_turns_still_returns_segment_annotations(self):
        segments = [_seg("a0", 0.0, 1.0, speaker="A", text="hi")]
        result = analyze(segments, [])
        assert len(result.segment_interactions) == 1
        assert result.segment_interactions[0].segment_id == "a0"
        assert result.segment_interactions[0].hesitation_before == 0.0


class TestPerformanceAtScale:
    """Lock in the indexed-lookup + sweep-line optimization. The original
    O(M² × N) implementation hung the interaction stage at 97% on hour-long
    meetings (~750 segments, ~1000 turns). With the index + sweep this should
    run in well under a second."""

    def test_thousand_turns_completes_quickly(self):
        import time

        # 1000 non-overlapping turns alternating between two speakers,
        # with 1000 matching transcript segments
        turns = []
        segments = []
        for i in range(1000):
            spk = "A" if i % 2 == 0 else "B"
            start = i * 1.0
            end = start + 0.9
            turns.append((start, end, spk))
            segments.append(_seg(f"s{i:04d}", start, end, speaker=spk, text="some words here"))

        t0 = time.monotonic()
        result = analyze(segments, turns)
        elapsed = time.monotonic() - t0

        assert len(result.segment_interactions) == 1000
        # Generous bound — the original implementation took minutes here
        assert elapsed < 2.0, f"analyze() took {elapsed:.2f}s on 1000 non-overlapping turns"
