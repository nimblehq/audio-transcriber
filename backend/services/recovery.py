from __future__ import annotations

import json
import logging

from config import MEETINGS_DIR

logger = logging.getLogger(__name__)


def recover_stuck_meetings() -> list[str]:
    """Scan all meetings and transition any with status=PROCESSING to ERROR.

    Returns a list of recovered meeting IDs.
    """
    recovered: list[str] = []

    for metadata_path in MEETINGS_DIR.glob("*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        if metadata.get("status") != "processing":
            continue

        meeting_id = metadata.get("id", metadata_path.parent.name)

        try:
            metadata["status"] = "error"
            metadata["error"] = "Transcription interrupted by app restart"
            metadata_path.write_text(json.dumps(metadata, indent=2))
        except OSError:
            logger.exception("Failed to update metadata for meeting: %s", meeting_id)
            continue

        recovered.append(meeting_id)
        logger.info("Recovered stuck meeting: %s", meeting_id)

    if recovered:
        logger.info("Recovered %d stuck meeting(s)", len(recovered))

    return recovered
