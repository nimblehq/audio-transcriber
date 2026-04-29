from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol

from backend.schemas import (
    InteractionEvent,
    InteractionEventType,
    SegmentInteraction,
)

logger = logging.getLogger(__name__)

# A segment is a back-channel when it's short AND its text is dominated by
# acknowledgement tokens. Both conditions are required to avoid false positives
# on short content words ("Tuesday") and on long agreement statements.
BACKCHANNEL_MAX_DURATION = 1.5
BACKCHANNEL_MAX_WORDS = 3
BACKCHANNEL_TOKENS = frozenset(
    {
        "uh-huh",
        "uhhuh",
        "uh",
        "huh",
        "mm-hmm",
        "mmhmm",
        "mhm",
        "mm",
        "yeah",
        "yep",
        "yup",
        "yes",
        "ok",
        "okay",
        "right",
        "sure",
        "wow",
        "i see",
        "got it",
        "exactly",
        "true",
    }
)

HESITATION_MIN_SECONDS = 0.7
LONG_PAUSE_MIN_SECONDS = 3.0

DOMINANT_SPEAKER_THRESHOLD = 0.8

CONTEXT_MAX_CHARS = 120


class _Segment(Protocol):
    id: str
    start: float
    end: float
    speaker: str
    text: str


@dataclass
class InteractionAnalysisResult:
    events: list[InteractionEvent] = field(default_factory=list)
    segment_interactions: list[SegmentInteraction] = field(default_factory=list)
    dominant_speaker_limitation: bool = False


def _normalize_text(text: str) -> str:
    return text.lower().strip().strip(".,!?-").strip()


def _is_backchannel_text(text: str) -> bool:
    """Lexical half of the back-channel heuristic."""
    normalized = _normalize_text(text)
    if not normalized:
        return False
    if normalized in BACKCHANNEL_TOKENS:
        return True
    words = normalized.split()
    if len(words) <= BACKCHANNEL_MAX_WORDS and any(w in BACKCHANNEL_TOKENS for w in words):
        return True
    return False


def _segment_at(
    timestamp: float,
    segments: list[_Segment],
    speaker: str | None = None,
) -> _Segment | None:
    """Locate the transcript segment containing `timestamp`.

    When `speaker` is given, only segments matching that speaker are considered —
    important for overlapping turns where multiple transcript segments cover the
    same timestamp. Falls back to the nearest segment by edge distance when no
    segment strictly contains the timestamp (gaps between WhisperX segments are
    common).
    """
    if not segments:
        return None
    candidates = [s for s in segments if speaker is None or s.speaker == speaker]
    if not candidates:
        return None
    for seg in candidates:
        if seg.start <= timestamp <= seg.end:
            return seg
    return min(
        candidates,
        key=lambda s: min(abs(s.start - timestamp), abs(s.end - timestamp)),
    )


def _text_at(timestamp: float, segments: list[_Segment], speaker: str | None = None) -> str:
    seg = _segment_at(timestamp, segments, speaker=speaker)
    return seg.text[:CONTEXT_MAX_CHARS] if seg else ""


def _detect_overlaps(
    diarize_turns: list[tuple[float, float, str]],
    transcript_segments: list[_Segment],
) -> list[InteractionEvent]:
    """Walk diarization turns and emit one event per cross-speaker overlap.

    Each pair (a, b) where `b` starts before `a` ends and they have different
    speakers produces either an `interruption` (default) or `overlap` event
    (when `b` is a back-channel — see TD-2).
    """
    events: list[InteractionEvent] = []
    sorted_turns = sorted(diarize_turns, key=lambda t: t[0])

    for i, (start_b, end_b, spk_b) in enumerate(sorted_turns):
        for start_a, end_a, spk_a in sorted_turns[:i]:
            if spk_a == spk_b:
                continue
            if start_b >= end_a:
                continue
            # b starts before a ends → overlap
            overlap_start = max(start_a, start_b)
            overlap_end = min(end_a, end_b)
            duration = max(0.0, overlap_end - overlap_start)

            duration_b = end_b - start_b
            text_b = _text_at((start_b + end_b) / 2, transcript_segments, speaker=spk_b)
            is_backchannel = duration_b <= BACKCHANNEL_MAX_DURATION and _is_backchannel_text(text_b)

            event_type = InteractionEventType.OVERLAP if is_backchannel else InteractionEventType.INTERRUPTION
            events.append(
                InteractionEvent(
                    event_type=event_type,
                    timestamp=round(start_b, 2),
                    speaker_a=spk_a,
                    speaker_b=spk_b,
                    duration=round(duration, 2),
                    context=text_b,
                )
            )

    return events


def _detect_pause_events(
    diarize_turns: list[tuple[float, float, str]],
    transcript_segments: list[_Segment],
) -> list[InteractionEvent]:
    """Emit hesitation/long_pause events for cross-speaker gaps above threshold."""
    events: list[InteractionEvent] = []
    sorted_turns = sorted(diarize_turns, key=lambda t: t[0])

    for prev, curr in zip(sorted_turns, sorted_turns[1:]):
        prev_start, prev_end, prev_spk = prev
        curr_start, _, curr_spk = curr
        if prev_spk == curr_spk:
            continue
        gap = curr_start - prev_end
        if gap < HESITATION_MIN_SECONDS:
            continue

        event_type = (
            InteractionEventType.LONG_PAUSE if gap >= LONG_PAUSE_MIN_SECONDS else InteractionEventType.HESITATION
        )
        events.append(
            InteractionEvent(
                event_type=event_type,
                timestamp=round(prev_end, 2),
                speaker_a=prev_spk,
                speaker_b=curr_spk,
                duration=round(gap, 2),
                context=_text_at(curr_start, transcript_segments, speaker=curr_spk),
            )
        )

    return events


def _build_segment_interactions(
    transcript_segments: list[_Segment],
    diarize_turns: list[tuple[float, float, str]],
    interruption_events: list[InteractionEvent],
) -> list[SegmentInteraction]:
    """Per-segment annotations: hesitation_before + interruption flags."""
    sorted_turns = sorted(diarize_turns, key=lambda t: t[0])

    # hesitation_before: distance from the most recent prior turn (any speaker).
    # Using turn timestamps rather than transcript segment edges so the value
    # reflects the actual silence in the room, not transcript chunking.
    annotations: dict[str, SegmentInteraction] = {
        seg.id: SegmentInteraction(segment_id=seg.id) for seg in transcript_segments
    }

    for seg in transcript_segments:
        prior_end = max(
            (t_end for t_start, t_end, _ in sorted_turns if t_end <= seg.start),
            default=None,
        )
        if prior_end is not None:
            annotations[seg.id].hesitation_before = round(max(0.0, seg.start - prior_end), 2)

    for event in interruption_events:
        if event.event_type != InteractionEventType.INTERRUPTION:
            continue
        # Interrupter (speaker_b) starts during the interrupted speaker's (a) turn.
        # Speaker-aware lookup matters because both transcript segments cover the
        # event timestamp during the overlap window.
        interrupter_seg = _segment_at(event.timestamp, transcript_segments, speaker=event.speaker_b)
        interrupted_seg = _segment_at(event.timestamp, transcript_segments, speaker=event.speaker_a)
        if interrupter_seg is not None and interrupter_seg.id in annotations:
            annotations[interrupter_seg.id].preceded_by_interruption = True
        if interrupted_seg is not None and interrupted_seg.id in annotations:
            annotations[interrupted_seg.id].followed_by_interruption = True

    return [annotations[seg.id] for seg in transcript_segments]


def _check_dominance(transcript_segments: list[_Segment]) -> bool:
    """True when one speaker accounts for more than 80% of total speaking time."""
    totals: dict[str, float] = {}
    grand_total = 0.0
    for seg in transcript_segments:
        duration = max(0.0, seg.end - seg.start)
        totals[seg.speaker] = totals.get(seg.speaker, 0.0) + duration
        grand_total += duration
    if grand_total <= 0.0:
        return False
    return max(totals.values()) / grand_total > DOMINANT_SPEAKER_THRESHOLD


def analyze(
    transcript_segments: Iterable[_Segment],
    diarize_turns: Iterable[tuple[float, float, str]],
) -> InteractionAnalysisResult:
    """Detect interaction patterns from PyAnnote diarization turns.

    `diarize_turns` are the raw, possibly-overlapping speaker turns from
    PyAnnote (after WhisperX collapses them via `assign_word_speakers`, the
    overlap data is gone — so this function expects the raw form). Transcript
    segments are used for context strings, back-channel text lookup, and the
    per-segment annotation output.
    """
    segments = list(transcript_segments)
    turns = list(diarize_turns)

    overlap_events = _detect_overlaps(turns, segments)
    pause_events = _detect_pause_events(turns, segments)
    events = sorted(overlap_events + pause_events, key=lambda e: e.timestamp)

    segment_interactions = _build_segment_interactions(segments, turns, overlap_events)
    dominant = _check_dominance(segments)

    return InteractionAnalysisResult(
        events=events,
        segment_interactions=segment_interactions,
        dominant_speaker_limitation=dominant,
    )
