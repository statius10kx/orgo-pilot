"""
Handles video assembly. Uses a portable ffmpeg binary via ffmpeg_util.
"""

import subprocess
from pathlib import Path

import ffmpeg

from orgolab.infra.ffmpeg import ensure_ffmpeg


class FFmpegFailure(RuntimeError):
    def __init__(self, message: str, log_path: Path):
        super().__init__(message)
        self.log_path = log_path


def build_video(frames_dir: Path, fps: float = 10.0) -> Path:
    """Stitch screenshot frames into video.mp4 using ffmpeg.

    Accepts .png or .jpg, whichever the first frame uses.
    """
    frames = sorted(frames_dir.glob("frame_*.*"))
    if not frames:
        raise RuntimeError(f"No frames found in {frames_dir}")

    first_ext = frames[0].suffix  # ".png" or ".jpg"
    input_pattern = str(frames_dir / f"frame_%04d{first_ext}")

    output_path = frames_dir.parent / "video.mp4"
    ffmpeg_exe = ensure_ffmpeg()

    try:
        # Get the command that would be run
        stream = (
            ffmpeg
            .input(input_pattern, framerate=fps)
            .output(str(output_path), pix_fmt="yuv420p")
            .overwrite_output()
        )
        cmd = stream.compile(cmd=ffmpeg_exe)

        # Run it manually to capture stderr
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # Save full log for debugging
            log_path = frames_dir.parent / "ffmpeg.log"
            with open(log_path, "w") as f:
                f.write(result.stderr)

            # Include the first few stderr lines for easier diagnosis
            snippet = result.stderr.splitlines()[:10]
            raise FFmpegFailure("FFmpeg failed:\n" + "\n".join(snippet), log_path)

    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        else:
            raise RuntimeError(f"FFmpeg execution error: {e}") from e

    return output_path
