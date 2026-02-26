import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=False)

BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
MEETINGS_DIR = DATA_DIR / "meetings"
TEMPLATES_DIR = BASE_DIR / "templates"

HF_TOKEN = os.getenv("HF_TOKEN", "")

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")
WHISPER_BATCH_SIZE = int(os.getenv("WHISPER_BATCH_SIZE", "16"))

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(500 * 1024 * 1024)))  # 500MB

MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
