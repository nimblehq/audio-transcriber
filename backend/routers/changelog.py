from __future__ import annotations

from fastapi import APIRouter

from backend.schemas import ChangelogResponse
from backend.services import changelog

router = APIRouter()


@router.get("/changelog", response_model=ChangelogResponse)
async def get_changelog() -> ChangelogResponse:
    # Degrades to an empty response (HTTP 200) when the changelog is missing,
    # so the optional "What's new" panel simply shows nothing.
    return changelog.get_changelog()
