from fastapi import APIRouter, HTTPException

from backend.schemas import AnalysisRequest
from backend.services.analyzer import generate_analysis
from config import MEETINGS_DIR

router = APIRouter()


@router.post("/meetings/{meeting_id}/analysis")
async def create_analysis(meeting_id: str, request: AnalysisRequest):
    meeting_dir = MEETINGS_DIR / meeting_id
    if not meeting_dir.exists():
        raise HTTPException(status_code=404, detail="Meeting not found")

    transcript_path = meeting_dir / "transcript.json"
    if not transcript_path.exists():
        raise HTTPException(status_code=400, detail="Transcript not ready yet")

    try:
        text = await generate_analysis(meeting_id, request.meeting_type)
        return {"analysis": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meetings/{meeting_id}/analysis")
async def get_analysis(meeting_id: str):
    meeting_dir = MEETINGS_DIR / meeting_id
    if not meeting_dir.exists():
        raise HTTPException(status_code=404, detail="Meeting not found")

    analysis_path = meeting_dir / "analysis.md"
    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="No analysis generated yet")

    return {"analysis": analysis_path.read_text(encoding="utf-8")}
