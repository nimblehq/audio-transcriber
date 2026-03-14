from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Isolated data directory for a single test."""
    meetings_dir = tmp_path / "meetings"
    meetings_dir.mkdir()
    return tmp_path


@pytest.fixture
def meetings_dir(data_dir: Path) -> Path:
    return data_dir / "meetings"


@pytest.fixture
async def client(data_dir: Path) -> AsyncClient:
    """Async test client with DATA_DIR patched to tmp_path."""
    import config as config_module
    from backend.main import app

    original_data_dir = config_module.DATA_DIR
    original_meetings_dir = config_module.MEETINGS_DIR

    config_module.DATA_DIR = data_dir
    config_module.MEETINGS_DIR = data_dir / "meetings"

    # Also patch the routers module that may have imported these
    import backend.routers.meetings as meetings_module

    original_router_meetings_dir = getattr(meetings_module, "MEETINGS_DIR", None)
    meetings_module.MEETINGS_DIR = data_dir / "meetings"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    config_module.DATA_DIR = original_data_dir
    config_module.MEETINGS_DIR = original_meetings_dir
    if original_router_meetings_dir is not None:
        meetings_module.MEETINGS_DIR = original_router_meetings_dir


@pytest.fixture
def sample_audio() -> Path:
    """Path to the minimal WAV fixture file."""
    return FIXTURES_DIR / "sample.wav"


@pytest.fixture
def sample_metadata() -> dict:
    """READY-state metadata as a dict."""
    return json.loads((FIXTURES_DIR / "metadata.json").read_text())


@pytest.fixture
def sample_metadata_processing() -> dict:
    """PROCESSING-state metadata as a dict."""
    return json.loads((FIXTURES_DIR / "metadata_processing.json").read_text())


@pytest.fixture
def sample_metadata_error() -> dict:
    """ERROR-state metadata as a dict."""
    return json.loads((FIXTURES_DIR / "metadata_error.json").read_text())


@pytest.fixture
def sample_transcript() -> dict:
    """Transcript with 4 segments and 2 speakers."""
    return json.loads((FIXTURES_DIR / "transcript.json").read_text())


@pytest.fixture
def populated_meeting(meetings_dir: Path, sample_metadata: dict, sample_transcript: dict, sample_audio: Path) -> str:
    """Create a fully populated meeting on disk. Returns the meeting ID."""
    meeting_id = sample_metadata["id"]
    meeting_dir = meetings_dir / meeting_id
    meeting_dir.mkdir()

    (meeting_dir / "metadata.json").write_text(json.dumps(sample_metadata))
    (meeting_dir / "transcript.json").write_text(json.dumps(sample_transcript))
    shutil.copy(sample_audio, meeting_dir / sample_metadata["audio_filename"])

    return meeting_id
