from __future__ import annotations

import json
from pathlib import Path

from app.models import LeadRecord


class LeadStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, session_id: str, lead: LeadRecord) -> None:
        payload = {"session_id": session_id, **lead.model_dump()}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

