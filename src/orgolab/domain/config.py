import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Centralized configuration for OrgoLab."""

    # Orgo API credentials
    orgo_project_id: str = Field(default_factory=lambda: os.getenv("ORGO_PROJECT_ID", ""))
    orgo_api_key: str = Field(default_factory=lambda: os.getenv("ORGO_API_KEY", ""))

    # Execution settings
    max_run_seconds: int = Field(default_factory=lambda: int(os.getenv("MAX_RUN_SECONDS", "180")))
    max_steps: int = 40
    action_cap: int = 40  # matches dashboard badge

    # Model settings
    claude_model: str = "claude-3-7-sonnet-20250219"
    thinking_enabled: bool = True

    # Display settings
    display_width: int = 1024
    display_height: int = 768

    # Paths
    artifacts_dir: str = "artifacts"

    class Config:
        validate_assignment = True
