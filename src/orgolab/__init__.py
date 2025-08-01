"""OrgoLab - Computer automation testing framework."""

# Import for backward compatibility
from orgolab.api import app
from orgolab.core import executor, replay
from orgolab.core.event_capture import extract_actions
from orgolab.domain.models import Run
from orgolab.infra.artifacts import FFmpegFailure, build_video
from orgolab.infra.ffmpeg import ensure_ffmpeg

# Re-export artifacts module at top level for tests
artifacts = type('module', (), {
    'build_video': build_video,
    'FFmpegFailure': FFmpegFailure
})

# Re-export models at top level
models = type('module', (), {
    'Run': Run
})

# Re-export event_capture at top level
event_capture = type('module', (), {
    'extract_actions': extract_actions
})

# Re-export ffmpeg_util at top level
ffmpeg_util = type('module', (), {
    'ensure_ffmpeg': ensure_ffmpeg
})

import sys
sys.modules['orgolab.artifacts'] = artifacts
sys.modules['orgolab.models'] = models
sys.modules['orgolab.event_capture'] = event_capture
sys.modules['orgolab.ffmpeg_util'] = ffmpeg_util

__version__ = "0.1.0"

__all__ = [
    "app",
    "executor", 
    "replay",
    "extract_actions",
    "Run",
    "FFmpegFailure",
    "build_video",
]