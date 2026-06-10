"""Per-chunk multilingual transcription (BR-4 through BR-7).

When a meeting declares two or more expected languages, each VAD speech chunk is
detected independently — constrained to the selected set — and transcribed in its
detected language. Chunks too short or too ambiguous to classify fall back to the
meeting's dominant (duration-weighted) language.

This module keeps all heavy ML imports lazy (inside functions) so the pure
classification helpers can be imported and unit-tested without whisperx, torch, or
numpy installed.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Iterable

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000

# Per-chunk classification policy (heuristic, tunable — not spec-derived).
# A chunk is classified only when it is long enough AND the most probable language
# within the selected set is clearly ahead; otherwise it falls back to the dominant
# language (BR-6).
LANG_MIN_CHUNK_SEC = 1.5
LANG_CONF_THRESHOLD = 0.70  # confidence renormalized within the selected set
LANG_RAW_FLOOR = 0.5  # absolute probability floor (rejects mostly-silence chunks)


def _constrained_language(
    all_probs: Iterable[tuple[str, float]] | dict[str, float],
    selected: set[str],
) -> tuple[str, float, float]:
    """Pick the most probable language within the selected set (BR-5).

    Returns ``(language, confidence_within_set, raw_probability)``. The candidate is
    always a member of ``selected`` — never an unselected language. Ties break
    deterministically (alphabetically).
    """
    probs = dict(all_probs)
    subset = {code: probs.get(code, 0.0) for code in selected}
    total = sum(subset.values()) or 1.0
    language = max(sorted(subset), key=lambda code: subset[code])
    return language, subset[language] / total, subset[language]


def _classify_chunk(
    all_probs: Iterable[tuple[str, float]] | dict[str, float],
    selected: set[str],
    duration: float,
) -> str | None:
    """Return the chunk's detected language, or None if too short/ambiguous (BR-6)."""
    if duration < LANG_MIN_CHUNK_SEC:
        return None
    language, confidence, raw = _constrained_language(all_probs, selected)
    if confidence >= LANG_CONF_THRESHOLD and raw >= LANG_RAW_FLOOR:
        return language
    return None


def _dominant_language(classified: Iterable[tuple[str | None, float]], selected: set[str]) -> str:
    """Duration-weighted dominant language over confidently-classified chunks (BR-6).

    ``classified`` is an iterable of ``(language_or_none, duration)``. Falls back to a
    deterministic pick from the selected set when nothing was classified.
    """
    weights: dict[str, float] = defaultdict(float)
    for language, duration in classified:
        if language:
            weights[language] += duration
    if weights:
        return max(sorted(weights), key=lambda code: weights[code])
    return sorted(selected)[0]


def _vad_chunks(audio, pipeline) -> list[dict]:
    """Reproduce WhisperX's VAD chunking outside ``.transcribe()``.

    Returns a list of ``{"start": float, "end": float}`` in seconds. Guarded against
    whisperx version drift in the VAD subpackage layout.
    """
    try:
        from whisperx.vads.vad import Vad
    except Exception:  # pragma: no cover - import shape varies across whisperx versions
        Vad = None

    vad_model = pipeline.vad_model
    if Vad is not None and isinstance(vad_model, Vad):
        preprocess_audio = vad_model.preprocess_audio
        merge_chunks = vad_model.merge_chunks
    else:  # pragma: no cover - fallback for the default Pyannote VAD path
        from whisperx.vads.pyannote import Pyannote

        preprocess_audio = Pyannote.preprocess_audio
        merge_chunks = Pyannote.merge_chunks

    waveform = preprocess_audio(audio)
    raw_segments = vad_model({"waveform": waveform, "sample_rate": SAMPLE_RATE})
    params = pipeline._vad_params
    merged = merge_chunks(
        raw_segments,
        chunk_size=params["chunk_size"],
        onset=params["vad_onset"],
        offset=params["vad_offset"],
    )
    return [{"start": float(chunk["start"]), "end": float(chunk["end"])} for chunk in merged]


def transcribe_multilingual(
    audio,
    selected_languages: set[str],
    pipeline,
    progress_cb: Callable[[int], None] | None = None,
) -> tuple[list[dict], str]:
    """Detect and transcribe each VAD speech chunk in its own language (BR-4..BR-7).

    ``pipeline`` is a whisperx ``FasterWhisperPipeline``; ``pipeline.model`` is the
    underlying faster-whisper ``WhisperModel`` used for both detection and decode.

    Returns ``(segments, dominant_language)`` where each segment is a dict with keys
    ``start``, ``end``, ``text``, ``language`` (timestamps are chunk-relative offsets
    folded back to absolute meeting time).
    """
    selected = set(selected_languages)

    def _progress(pct: int) -> None:
        if progress_cb is not None:
            progress_cb(pct)

    _progress(20)
    chunks = _vad_chunks(audio, pipeline)
    if not chunks:
        return [], sorted(selected)[0]

    model = pipeline.model

    # Pass 1: constrained per-chunk language detection.
    scored: list[dict] = []
    for chunk in chunks:
        start, end = chunk["start"], chunk["end"]
        duration = end - start
        chunk_audio = audio[int(start * SAMPLE_RATE) : int(end * SAMPLE_RATE)]
        language = None
        if duration >= LANG_MIN_CHUNK_SEC and len(chunk_audio) > 0:
            try:
                _, _, all_probs = model.detect_language(audio=chunk_audio)
                language = _classify_chunk(all_probs, selected, duration)
            except Exception:
                logger.exception("Per-chunk language detection failed; deferring to dominant language")
        scored.append({"start": start, "end": end, "audio": chunk_audio, "language": language})

    _progress(35)

    # Resolve the dominant language and assign it to every unclassified chunk (BR-6).
    dominant = _dominant_language([(c["language"], c["end"] - c["start"]) for c in scored], selected)
    for chunk in scored:
        if chunk["language"] is None:
            chunk["language"] = dominant

    # Pass 2: transcribe each chunk in its final language (BR-4, BR-7).
    segments: list[dict] = []
    total = len(scored)
    for index, chunk in enumerate(scored):
        try:
            fw_segments, _info = model.transcribe(chunk["audio"], language=chunk["language"], vad_filter=False)
            for fw in fw_segments:
                text = (fw.text or "").strip()
                if not text:
                    continue
                segments.append(
                    {
                        "start": chunk["start"] + float(fw.start),
                        "end": chunk["start"] + float(fw.end),
                        "text": text,
                        "language": chunk["language"],
                    }
                )
        except Exception:
            logger.exception("Per-chunk transcription failed for chunk at %.2fs", chunk["start"])
        if total:
            _progress(35 + int((index + 1) / total * 53))  # 35 -> 88

    return segments, dominant
