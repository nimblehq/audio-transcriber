from __future__ import annotations

import json
import logging
from pathlib import Path

import anthropic

from backend.schemas import MeetingMetadata, MeetingType, Transcript
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MEETINGS_DIR, TEMPLATES_DIR

logger = logging.getLogger(__name__)

TEMPLATE_FILES = {
    MeetingType.INTERVIEW: "interview_analysis.md",
    MeetingType.SALES: "sales_meeting_analysis.md",
    MeetingType.CLIENT: "client_meeting_analysis.md",
    MeetingType.OTHER: "other.md",
}


def _load_template(meeting_type: MeetingType) -> str:
    filename = TEMPLATE_FILES.get(meeting_type)
    if not filename:
        filename = "other.md"
    template_path = TEMPLATES_DIR / filename
    if not template_path.exists():
        return "Analyze this meeting transcript and provide a structured summary with key decisions, action items, and notable quotes."
    return template_path.read_text(encoding="utf-8")


def _format_transcript_for_analysis(transcript: Transcript, speakers: dict[str, str]) -> str:
    lines = []
    for seg in transcript.segments:
        speaker_name = speakers.get(seg.speaker, seg.speaker)
        minutes = int(seg.start // 60)
        seconds = int(seg.start % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        lines.append(f"[{timestamp}] {speaker_name}: {seg.text}")
    return "\n".join(lines)


async def generate_analysis(meeting_id: str, meeting_type: MeetingType | None = None) -> str:
    meeting_dir = MEETINGS_DIR / meeting_id

    with open(meeting_dir / "metadata.json") as f:
        metadata = MeetingMetadata(**json.load(f))

    with open(meeting_dir / "transcript.json") as f:
        transcript = Transcript(**json.load(f))

    effective_type = meeting_type or metadata.type
    template = _load_template(effective_type)
    formatted_transcript = _format_transcript_for_analysis(transcript, metadata.speakers)

    prompt = f"{template}\n\n## Transcript\n\n{formatted_transcript}"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    analysis_text = message.content[0].text

    # Save analysis
    analysis_path = meeting_dir / "analysis.md"
    analysis_path.write_text(analysis_text, encoding="utf-8")

    # Update metadata type if changed
    if meeting_type and meeting_type != metadata.type:
        metadata.type = meeting_type
        with open(meeting_dir / "metadata.json", "w") as f:
            json.dump(metadata.model_dump(mode="json"), f, ensure_ascii=False, indent=2, default=str)

    return analysis_text
