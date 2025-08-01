from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class Run(BaseModel):
    id: UUID
    target_url: HttpUrl
    status: Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED", "ERROR"]
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    accepted: bool = False
    looped: bool = False
    video_path: Optional[str] = None
    error: Optional[str] = None
    seconds_per_frame: float = 0.1
    log_path: Optional[str] = None
    intent: Optional[str] = None
    success: list[str] | None = None         # natural-language assertions
    context: dict | None = None              # creds / seed data / flags
    outcome: Literal["SUCCESS", "ASSERTION_FAIL", "DESIGN_FAIL"] | None = None
    artifact_files: list[str] | None = None  # filenames only

    def dict_json(self):
        return self.model_dump(mode="json")
