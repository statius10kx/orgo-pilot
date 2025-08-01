"""Image processing utilities for OrgoLab."""

import base64
from pathlib import Path
from typing import Any, Dict, List


def guess_ext(buf: bytes) -> str:
    """Return image extension based on header bytes."""
    if buf.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if buf.startswith(b"\xff\xd8\xff"):
        return "jpg"
    raise ValueError("Unknown image format")


def save_base64_blocks(blocks: List[Dict[str, Any]], dest_dir: Path, prefix: str = "frame") -> int:
    """Extract and save all base64 images from a list of blocks.

    Returns the number of images saved.
    """
    counter = 0
    existing = len([p for ext in ("png", "jpg") for p in dest_dir.glob(f"{prefix}_*.{ext}")])

    for block in blocks:
        if block.get("type") == "image":
            src = block.get("source", {})
            if src.get("type") == "base64":
                raw = base64.b64decode(src["data"])
                ext = guess_ext(raw)
                (dest_dir / f"{prefix}_{existing + counter:04d}.{ext}").write_bytes(raw)
                counter += 1

    return counter


def walk_and_save_images(msg: Any, dest_dir: Path, counter_ref: List[int]) -> None:
    """Recursively walk a message structure and save all base64 images."""
    if isinstance(msg, dict):
        if msg.get("type") == "image":
            src = msg.get("source", {})
            if src.get("type") == "base64":
                raw = base64.b64decode(src["data"])
                ext = guess_ext(raw)
                (dest_dir / f"frame_{counter_ref[0]:04d}.{ext}").write_bytes(raw)
                counter_ref[0] += 1
        for v in msg.values():
            if isinstance(v, (dict, list)):
                walk_and_save_images(v, dest_dir, counter_ref)
    elif isinstance(msg, list):
        for item in msg:
            walk_and_save_images(item, dest_dir, counter_ref)
