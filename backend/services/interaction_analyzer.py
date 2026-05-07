from __future__ import annotations

import bisect
import heapq
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

# A turn is a back-channel when it's short AND its text is dominated by
# acknowledgement tokens. Both conditions together avoid false positives on
# short content words ("Tuesday") and on long agreement statements.
#
# A duration-only floor catches cases where the lexicon doesn't (production
# logs surfaced sub-second "Nice." / "Cool." utterances escaping the lexical
# filter): any utterance ≤ 0.5s with ≤ 2 words is treated as a back-channel
# regardless of vocabulary.
BACKCHANNEL_MAX_DURATION = 1.5
BACKCHANNEL_MAX_WORDS = 3
BACKCHANNEL_SHORT_DURATION = 0.5
BACKCHANNEL_SHORT_MAX_WORDS = 2
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
        "hmm",
        "oh",
        "ah",
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
        "nice",
        "cool",
        "great",
        "perfect",
        "awesome",
        "totally",
        "indeed",
        "agreed",
        "makes sense",
        "fair enough",
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


def _is_backchannel(duration: float, text: str) -> bool:
    """Combined back-channel heuristic. A turn is a back-channel when:

    - it's sub-floor (≤ 0.5s) AND has no transcript text (PyAnnote split a
      brief vocalization that WhisperX didn't deem worth transcribing — this
      is the dominant pattern for false-positive interruptions in real audio), OR
    - it's sub-floor with at most two words (catches "Nice." / "Cool." that
      escape the lexicon), OR
    - it's within the duration cap and lexically matches an acknowledgement.
    """
    normalized = _normalize_text(text)
    word_count = len(normalized.split())
    if duration <= BACKCHANNEL_SHORT_DURATION:
        if word_count == 0:
            return True
        if word_count <= BACKCHANNEL_SHORT_MAX_WORDS:
            return True
    return duration <= BACKCHANNEL_MAX_DURATION and _is_backchannel_text(text)


@dataclass
class _SegmentIndex:
    """Per-speaker index of transcript segments sorted by start time.

    Built once at the top of `analyze()` so the per-pair text lookups inside
    `_detect_overlaps` are O(log N) instead of O(N) — the original linear scan
    + per-call list comprehension was O(M² × N) overall, which made the
    interaction stage hang at 97% on hour-long meetings.
    """

    by_speaker: dict[str, list[_Segment]]
    by_speaker_starts: dict[str, list[float]]
    all_segments: list[_Segment]
    all_starts: list[float]

    @classmethod
    def build(cls, segments: list[_Segment]) -> _SegmentIndex:
        by_speaker: dict[str, list[_Segment]] = {}
        for seg in segments:
            by_speaker.setdefault(seg.speaker, []).append(seg)
        for lst in by_speaker.values():
            lst.sort(key=lambda s: s.start)
        all_sorted = sorted(segments, key=lambda s: s.start)
        return cls(
            by_speaker=by_speaker,
            by_speaker_starts={spk: [s.start for s in lst] for spk, lst in by_speaker.items()},
            all_segments=all_sorted,
            all_starts=[s.start for s in all_sorted],
        )

    def _lookup_in(self, timestamp: float, segs: list[_Segment], starts: list[float], strict: bool) -> _Segment | None:
        if not segs:
            return None
        # Rightmost segment whose start <= timestamp
        idx = bisect.bisect_right(starts, timestamp) - 1
        if 0 <= idx < len(segs) and segs[idx].start <= timestamp <= segs[idx].end:
            return segs[idx]
        if strict:
            return None
        # Lenient: nearest of the two adjacent candidates by edge distance
        before = segs[idx] if 0 <= idx < len(segs) else None
        after = segs[idx + 1] if 0 <= idx + 1 < len(segs) else None
        if before is None:
            return after
        if after is None:
            return before
        before_dist = min(abs(before.start - timestamp), abs(before.end - timestamp))
        after_dist = min(abs(after.start - timestamp), abs(after.end - timestamp))
        return before if before_dist <= after_dist else after

    def segment_at(self, timestamp: float, speaker: str | None = None, strict: bool = False) -> _Segment | None:
        if speaker is None:
            return self._lookup_in(timestamp, self.all_segments, self.all_starts, strict)
        segs = self.by_speaker.get(speaker, [])
        starts = self.by_speaker_starts.get(speaker, [])
        return self._lookup_in(timestamp, segs, starts, strict)

    def text_at(self, timestamp: float, speaker: str | None = None, strict: bool = False) -> str:
        seg = self.segment_at(timestamp, speaker=speaker, strict=strict)
        return seg.text[:CONTEXT_MAX_CHARS] if seg else ""


def _detect_overlaps(
    sorted_turns: list[tuple[float, float, str]],
    index: _SegmentIndex,
) -> list[InteractionEvent]:
    """Sweep-line overlap detection.

    Maintains a min-heap of currently-active turns (keyed by end time). For each
    new turn, prunes turns that have already ended, then iterates only the
    still-active set — turning the worst case from O(M²) into O(M × K) where K
    is the average overlap density (small for real meetings).
    """
    events: list[InteractionEvent] = []
    # Heap of (end_time, idx) for turns that haven't ended yet
    active: list[tuple[float, int]] = []

    for i, (start_b, end_b, spk_b) in enumerate(sorted_turns):
        # Drop turns that ended before this one started
        while active and active[0][0] <= start_b:
            heapq.heappop(active)

        midpoint = (start_b + end_b) / 2
        duration_b = end_b - start_b
        text_b_strict_cached: str | None = None
        text_b_lenient_cached: str | None = None

        for _, idx_a in active:
            start_a, end_a, spk_a = sorted_turns[idx_a]
            if spk_a == spk_b:
                continue
            # b started during a's turn (since a is still active)
            overlap_start = max(start_a, start_b)
            overlap_end = min(end_a, end_b)
            duration = max(0.0, overlap_end - overlap_start)

            # Lookups depend only on b's turn — same for every active a
            if text_b_strict_cached is None:
                text_b_strict_cached = index.text_at(midpoint, speaker=spk_b, strict=True)
            text_b_strict = text_b_strict_cached
            is_backchannel = _is_backchannel(duration_b, text_b_strict)
            if text_b_strict:
                text_b = text_b_strict
            else:
                if text_b_lenient_cached is None:
                    text_b_lenient_cached = index.text_at(midpoint, speaker=spk_b)
                text_b = text_b_lenient_cached

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

        heapq.heappush(active, (end_b, i))

    return events


def _detect_pause_events(
    sorted_turns: list[tuple[float, float, str]],
    index: _SegmentIndex,
) -> list[InteractionEvent]:
    """Emit hesitation/long_pause events for cross-speaker gaps above threshold."""
    events: list[InteractionEvent] = []

    for prev, curr in zip(sorted_turns, sorted_turns[1:]):
        _, prev_end, prev_spk = prev
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
                context=index.text_at(curr_start, speaker=curr_spk),
            )
        )

    return events


def _build_segment_interactions(
    transcript_segments: list[_Segment],
    sorted_turns: list[tuple[float, float, str]],
    interruption_events: list[InteractionEvent],
    index: _SegmentIndex,
) -> list[SegmentInteraction]:
    """Per-segment annotations: hesitation_before + interruption flags."""
    annotations: dict[str, SegmentInteraction] = {
        seg.id: SegmentInteraction(segment_id=seg.id) for seg in transcript_segments
    }

    # hesitation_before: distance from the most recent prior turn (any speaker).
    # Pre-sort turn ends and use bisect for O(log M) lookup per segment instead
    # of the original O(M) generator scan that was O(N × M) overall.
    sorted_ends = sorted(t[1] for t in sorted_turns)
    for seg in transcript_segments:
        idx = bisect.bisect_right(sorted_ends, seg.start) - 1
        if idx >= 0:
            annotations[seg.id].hesitation_before = round(max(0.0, seg.start - sorted_ends[idx]), 2)

    for event in interruption_events:
        if event.event_type != InteractionEventType.INTERRUPTION:
            continue
        # Interrupter (speaker_b) starts during the interrupted speaker's (a) turn.
        # Speaker-aware lookup matters because both transcript segments cover the
        # event timestamp during the overlap window.
        interrupter_seg = index.segment_at(event.timestamp, speaker=event.speaker_b)
        interrupted_seg = index.segment_at(event.timestamp, speaker=event.speaker_a)
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
    sorted_turns = sorted(diarize_turns, key=lambda t: t[0])
    index = _SegmentIndex.build(segments)

    overlap_events = _detect_overlaps(sorted_turns, index)
    pause_events = _detect_pause_events(sorted_turns, index)
    events = sorted(overlap_events + pause_events, key=lambda e: e.timestamp)

    segment_interactions = _build_segment_interactions(segments, sorted_turns, overlap_events, index)
    dominant = _check_dominance(segments)

    return InteractionAnalysisResult(
        events=events,
        segment_interactions=segment_interactions,
        dominant_speaker_limitation=dominant,
    )
