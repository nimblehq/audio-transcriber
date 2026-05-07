from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from backend.schemas import AudioAnalysis, AudioAnalysisStatus, MeetingMetadata, Transcript
from backend.services import analysis_context
from config import MEETINGS_DIR, TEMPLATES_DIR

router = APIRouter()

TEMPLATE_FILES = {
    "interview": "interview_analysis.md",
    "sales": "sales_meeting_analysis.md",
    "client": "client_meeting_analysis.md",
    "other": "other.md",
    "prototype": "prototype_scope.md",
}


@router.get("/templates/{template_type}")
async def get_template(template_type: str):
    filename = TEMPLATE_FILES.get(template_type)
    if not filename:
        raise HTTPException(status_code=404, detail="Template not found")

    template_path = TEMPLATES_DIR / filename
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template file not found")

    return {"template": template_path.read_text(encoding="utf-8")}


@router.get("/meetings/{meeting_id}/analysis-context")
async def get_analysis_context(meeting_id: str):
    """Return the rendered Audio Analysis Context markdown for a meeting.

    Returns an empty string when the meeting is opted out of audio analysis,
    so the analysis prompt remains byte-identical to the pre-feature output
    (BR-4.4). Returns a brief unavailability note when audio analysis was
    attempted but produced no usable output.
    """
    meeting_dir = MEETINGS_DIR / meeting_id
    metadata_path = meeting_dir / "metadata.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Meeting not found")

    metadata = MeetingMetadata(**json.loads(metadata_path.read_text(encoding="utf-8")))

    if not metadata.audio_analysis_enabled:
        return {"context": ""}

    audio_analysis_path = meeting_dir / "audio_analysis.json"
    if audio_analysis_path.exists():
        audio_analysis = AudioAnalysis(**json.loads(audio_analysis_path.read_text(encoding="utf-8")))
    else:
        # Opted in but no audio_analysis.json on disk — treat as unavailable so
        # the prompt discloses the gap (BR-4.5).
        audio_analysis = AudioAnalysis(
            status=AudioAnalysisStatus.UNAVAILABLE,
            reason="audio analysis has not produced output for this meeting",
        )

    transcript: Transcript | None = None
    transcript_path = meeting_dir / "transcript.json"
    if transcript_path.exists():
        transcript = Transcript(**json.loads(transcript_path.read_text(encoding="utf-8")))

    rendered = analysis_context.render(audio_analysis, transcript, speakers=metadata.speakers)
    return {"context": rendered}
