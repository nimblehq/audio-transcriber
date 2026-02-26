from fastapi import APIRouter, HTTPException

from config import TEMPLATES_DIR

router = APIRouter()

TEMPLATE_FILES = {
    "interview": "interview_analysis.md",
    "sales": "sales_meeting_analysis.md",
    "client": "client_meeting_analysis.md",
    "other": "other.md",
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
