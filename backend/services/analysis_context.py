"""Render the Audio Analysis Context section that gets injected into LLM
analysis prompts.

The output is a markdown string. When a meeting is opted out of audio
analysis, the function returns an empty string so the prompt stays
byte-identical to today's output (BR-4.4).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

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

# Confidence threshold below which any emotion claim is hedged (BR-4.2).
LOW_CONFIDENCE_THRESHOLD = 0.5

# Strong-signal threshold for surfacing emotional spikes.
SPIKE_CONFIDENCE_THRESHOLD = 0.7

# Energy-trajectory window size in seconds.
ENERGY_WINDOW_SECONDS = 300.0

# Maximum quoted excerpt length for word-tone mismatches.
MISMATCH_EXCERPT_CHARS = 80

# Phrases that read as agreement / acceptance in transcript text. When
# co-occurring with frustrated or uncertain tone, they form a word-tone
# mismatch worth surfacing.
AGREEMENT_PHRASES = (
    "works for me",
    "sounds good",
    "that's fine",
    "thats fine",
    "no concerns",
    "no issues",
    "no problem",
    "i agree",
    "agreed",
    "sure thing",
    "fine by me",
    "looks good",
    "all good",
    "happy with that",
    "i'm good",
    "im good",
    "makes sense",
    "i'm okay with",
    "im okay with",
    "i'm fine with",
    "im fine with",
)

MISMATCH_EMOTIONS = {EmotionCategory.FRUSTRATED, EmotionCategory.UNCERTAIN}

ENERGY_POSITIVE = {EmotionCategory.ENGAGED, EmotionCategory.CONFIDENT}
ENERGY_NEGATIVE = {EmotionCategory.DISENGAGED, EmotionCategory.FRUSTRATED}


def render(
    audio_analysis: AudioAnalysis | None,
    transcript: Transcript | None,
    speakers: dict[str, str] | None = None,
) -> str:
    """Render the Audio Analysis Context markdown block.

    Returns "" when the meeting is opted out of audio analysis (BR-4.4).
    Returns a short unavailability note when audio analysis was attempted but
    produced no output (failed or unavailable). Otherwise returns the full
    Audio Analysis Context section followed by template-agnostic LLM
    instructions on how to weight the signals.
    """
    if audio_analysis is None:
        return ""

    if audio_analysis.status != AudioAnalysisStatus.COMPLETED:
        return _render_unavailable(audio_analysis)

    speaker_names = speakers or {}
    segments_by_id = _index_segments(transcript)

    sections = [
        _render_emotional_patterns(audio_analysis.emotions, speaker_names),
        _render_word_tone_mismatches(audio_analysis.emotions, segments_by_id, speaker_names),
        _render_interaction_dynamics(
            audio_analysis.interactions,
            audio_analysis.segment_interactions,
            segments_by_id,
            speaker_names,
            audio_analysis.dominant_speaker_limitation,
        ),
        _render_energy_trajectory(audio_analysis.emotions),
    ]

    body = "\n\n".join(s for s in sections if s)
    if not body:
        return _render_unavailable(audio_analysis)

    return "## Audio Analysis Context\n\n" + body + "\n\n" + _instructions()


def _render_unavailable(audio_analysis: AudioAnalysis) -> str:
    reason = audio_analysis.reason or "audio analysis was not produced for this meeting"
    return (
        "## Audio Analysis Context\n\n"
        f"_Audio analysis was unavailable for this meeting ({reason}). Analyze the transcript "
        "without audio context._"
    )


def _index_segments(transcript: Transcript | None) -> dict[str, TranscriptSegment]:
    if transcript is None:
        return {}
    return {seg.id: seg for seg in transcript.segments}


def _display_speaker(speaker_id: str, speaker_names: dict[str, str]) -> str:
    return speaker_names.get(speaker_id, speaker_id)


def _format_timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def _render_emotional_patterns(
    emotions: list[EmotionAnnotation],
    speaker_names: dict[str, str],
) -> str:
    if not emotions:
        return ""

    by_speaker: dict[str, list[EmotionAnnotation]] = defaultdict(list)
    for ann in emotions:
        by_speaker[ann.speaker].append(ann)

    lines = ["### Emotional Patterns"]
    for speaker_id in sorted(by_speaker.keys()):
        anns = by_speaker[speaker_id]
        counter: Counter[EmotionCategory] = Counter(a.primary_emotion for a in anns)
        total = sum(counter.values())
        primary, primary_count = counter.most_common(1)[0]
        primary_pct = round(100 * primary_count / total)

        spikes = [
            a for a in anns if a.primary_emotion in MISMATCH_EMOTIONS and a.confidence >= SPIKE_CONFIDENCE_THRESHOLD
        ]
        spikes.sort(key=lambda a: a.start)
        spike_text = ""
        if spikes:
            spike_label = ", ".join(f"{a.primary_emotion.value} at {_format_timestamp(a.start)}" for a in spikes[:5])
            if len(spikes) > 5:
                spike_label += f" (+{len(spikes) - 5} more)"
            spike_text = f"; spikes: {spike_label}"

        name = _display_speaker(speaker_id, speaker_names)
        lines.append(f"- {name}: predominantly {primary.value} ({primary_pct}%){spike_text}")

    return "\n".join(lines)


def _excerpt(text: str, limit: int = MISMATCH_EXCERPT_CHARS) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _render_word_tone_mismatches(
    emotions: list[EmotionAnnotation],
    segments_by_id: dict[str, TranscriptSegment],
    speaker_names: dict[str, str],
) -> str:
    if not emotions or not segments_by_id:
        return ""

    matches: list[tuple[EmotionAnnotation, TranscriptSegment]] = []
    for ann in emotions:
        if ann.primary_emotion not in MISMATCH_EMOTIONS:
            continue
        seg = segments_by_id.get(ann.segment_id)
        if seg is None:
            continue
        if not _text_signals_agreement(seg.text):
            continue
        matches.append((ann, seg))

    if not matches:
        return ""

    matches.sort(key=lambda pair: pair[1].start)

    lines = ["### Word-Tone Mismatches"]
    for ann, seg in matches:
        name = _display_speaker(seg.speaker, speaker_names)
        verb = "may indicate" if ann.confidence < LOW_CONFIDENCE_THRESHOLD else "indicates"
        lines.append(
            f'- [{_format_timestamp(seg.start)}] {name}: "{_excerpt(seg.text)}" — '
            f"tone {verb} {ann.primary_emotion.value} (confidence: {ann.confidence:.2f})"
        )
    return "\n".join(lines)


def _text_signals_agreement(text: str) -> bool:
    normalized = text.lower()
    return any(phrase in normalized for phrase in AGREEMENT_PHRASES)


def _render_interaction_dynamics(
    events: list[InteractionEvent],
    segment_interactions: list[SegmentInteraction],
    segments_by_id: dict[str, TranscriptSegment],
    speaker_names: dict[str, str],
    dominant_speaker_limitation: bool,
) -> str:
    has_interactions = bool(events) or any(si.hesitation_before > 0 for si in segment_interactions)
    if not has_interactions and not dominant_speaker_limitation:
        return ""

    lines = ["### Interaction Dynamics"]

    interruptions = [e for e in events if e.event_type == InteractionEventType.INTERRUPTION]
    if interruptions:
        pair_counts: Counter[tuple[str, str]] = Counter()
        for ev in interruptions:
            pair_counts[(ev.speaker_b, ev.speaker_a)] += 1  # b interrupted a
        for (interrupter, interrupted), count in pair_counts.most_common(5):
            reverse = pair_counts.get((interrupted, interrupter), 0)
            i_name = _display_speaker(interrupter, speaker_names)
            t_name = _display_speaker(interrupted, speaker_names)
            lines.append(f"- {i_name} interrupted {t_name} {count} time{_s(count)} (reverse: {reverse})")

    latencies = _average_response_latency(segment_interactions, segments_by_id)
    if latencies:
        parts = [f"{_display_speaker(spk, speaker_names)} ({avg:.1f}s)" for spk, avg in latencies]
        lines.append(f"- Average response latency: {', '.join(parts)}")

    hesitations = [e for e in events if e.event_type == InteractionEventType.HESITATION]
    if hesitations:
        hesitations.sort(key=lambda e: e.duration, reverse=True)
        notable = hesitations[:3]
        for ev in notable:
            name = _display_speaker(ev.speaker_a, speaker_names)
            lines.append(f"- Notable hesitation: {name} paused {ev.duration:.1f}s at {_format_timestamp(ev.timestamp)}")

    if dominant_speaker_limitation:
        lines.append(
            "- _Limited interaction data: a single speaker dominates this meeting, "
            "so interruption and turn-taking signals are sparse._"
        )

    if len(lines) == 1:
        return ""
    return "\n".join(lines)


def _s(count: int) -> str:
    return "" if count == 1 else "s"


def _average_response_latency(
    segment_interactions: list[SegmentInteraction],
    segments_by_id: dict[str, TranscriptSegment],
) -> list[tuple[str, float]]:
    by_speaker: dict[str, list[float]] = defaultdict(list)
    for si in segment_interactions:
        if si.hesitation_before <= 0:
            continue
        seg = segments_by_id.get(si.segment_id)
        if seg is None:
            continue
        by_speaker[seg.speaker].append(si.hesitation_before)

    averages = [(spk, sum(vals) / len(vals)) for spk, vals in by_speaker.items() if vals]
    averages.sort(key=lambda pair: pair[0])
    return averages


def _render_energy_trajectory(emotions: list[EmotionAnnotation]) -> str:
    if not emotions:
        return ""

    end = max(a.end for a in emotions)
    if end <= 0:
        return ""

    windows: list[list[float]] = []
    n_windows = max(1, int(end // ENERGY_WINDOW_SECONDS) + 1)
    for _ in range(n_windows):
        windows.append([])

    for ann in emotions:
        idx = min(int(ann.start // ENERGY_WINDOW_SECONDS), n_windows - 1)
        windows[idx].append(_energy_score(ann))

    averaged = []
    for i, scores in enumerate(windows):
        if not scores:
            continue
        averaged.append((i, sum(scores) / len(scores)))

    if not averaged:
        return ""

    peak = max(averaged, key=lambda pair: pair[1])
    trough = min(averaged, key=lambda pair: pair[1])

    lines = ["### Energy Trajectory"]
    lines.append(f"- Energy peaked during {_window_label(peak[0])} (score {peak[1]:+.2f})")
    if trough[0] != peak[0]:
        lines.append(f"- Energy lowest during {_window_label(trough[0])} (score {trough[1]:+.2f})")
    return "\n".join(lines)


def _energy_score(ann: EmotionAnnotation) -> float:
    if ann.primary_emotion in ENERGY_POSITIVE:
        return ann.confidence
    if ann.primary_emotion in ENERGY_NEGATIVE:
        return -ann.confidence
    return 0.0


def _window_label(index: int) -> str:
    start = int(index * ENERGY_WINDOW_SECONDS)
    end = int(start + ENERGY_WINDOW_SECONDS)
    return f"{_format_timestamp(start)}–{_format_timestamp(end)}"


def _instructions() -> str:
    return (
        "## Audio Analysis Instructions\n\n"
        "Factor the audio context into your assessment alongside the transcript:\n\n"
        "1. **Hidden disagreements:** Weight word-tone mismatches heavily. Verbal "
        "agreement paired with frustrated or uncertain tone is likely not genuine "
        "alignment — flag it as an unresolved or potential issue rather than a "
        "settled point.\n"
        "2. **Contribution quality:** A confident assertion carries more influence "
        "than the same words said with uncertainty. Weight contributions by tone, "
        "not just volume of speech.\n"
        "3. **Psychological safety:** Hesitation patterns, asymmetric interruption "
        "counts, and one-directional dominance reveal power dynamics. Surface them "
        "when they affect who speaks freely and who self-censors.\n"
        "4. **Meeting effectiveness:** Track the energy trajectory. A meeting that "
        "ends in a low-energy or disengaged window is less likely to produce "
        "follow-through, regardless of the commitments made.\n\n"
        "Confidence levels are reported alongside emotional claims. Low-confidence "
        "claims are already hedged in the context above — preserve that hedging in "
        "your output rather than asserting them as fact.\n"
    )


__all__: Iterable[str] = ("render",)
