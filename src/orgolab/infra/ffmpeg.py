"""
Unified helper that guarantees we always have a working ffmpeg binary.

• First checks IMAGEIO_FFMPEG_EXE env var (user override).
• Then tries imageio_ffmpeg.get_ffmpeg_exe().
• On ARM Macs, ffmpeg must be installed via Homebrew: brew install ffmpeg
The resolved path is cached.
"""

import os
import platform
import shutil
from functools import lru_cache
from pathlib import Path

import imageio_ffmpeg


@lru_cache(maxsize=1)
def ensure_ffmpeg() -> str:
    # 1. Respect explicit override
    explicit = os.getenv("IMAGEIO_FFMPEG_EXE")
    if explicit and Path(explicit).exists():
        return explicit

    # 2. Try imageio cache
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ValueError, FileNotFoundError, RuntimeError):
        pass

    # 3. Check system PATH for ffmpeg
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 4. Platform-specific error messages
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin" and machine == "arm64":
        raise RuntimeError(
            "FFmpeg not found on Apple Silicon Mac.\n"
            "Please install via Homebrew:\n"
            "  brew install ffmpeg\n"
            "Or set IMAGEIO_FFMPEG_EXE environment variable to point to ffmpeg binary."
        )
    else:
        raise RuntimeError(
            "FFmpeg not found in system PATH.\n"
            "Please install ffmpeg:\n"
            "  - macOS: brew install ffmpeg\n"
            "  - Ubuntu/Debian: sudo apt-get install ffmpeg\n"
            "  - Windows: Download from https://ffmpeg.org/download.html\n"
            "Or set IMAGEIO_FFMPEG_EXE environment variable to point to ffmpeg binary."
        )
