import asyncio
import base64
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from orgo import Computer

from orgolab.core.artifacts import build_all
from orgolab.core.event_capture import extract_actions
from orgolab.core.images import guess_ext, walk_and_save_images
from orgolab.domain.config import Settings
from orgolab.domain.models import Run
from orgolab.infra.artifacts import FFmpegFailure, build_video
from orgolab.infra.store import update_run

# Load environment variables
load_dotenv()


def _contains_task_complete(msg) -> bool:
    """
    True if any tool_result with name == 'task_complete' appears anywhere
    in the nested message / event dict.
    """
    if isinstance(msg, dict):
        if msg.get("name") == "task_complete":
            return True
        for v in msg.values():
            if isinstance(v, (dict, list)) and _contains_task_complete(v):
                return True
    elif isinstance(msg, list):
        return any(_contains_task_complete(m) for m in msg)
    return False


async def run_test(run: Run, pc: Computer, *, cfg: Settings) -> None:
    try:
        # Update status to RUNNING
        run.status = "RUNNING"
        run.started_at = datetime.now(timezone.utc)
        await update_run(run)

        # Run with timeout
        await asyncio.wait_for(
            _run_test_inner(run, pc, cfg),
            timeout=cfg.max_run_seconds
        )

    except asyncio.TimeoutError:
        # Update run with timeout failure
        run.status = "ERROR"
        run.error = f"Test timed out after {cfg.max_run_seconds} seconds"
        run.finished_at = datetime.now(timezone.utc)
        await update_run(run)
    except Exception as exc:
        # Update run with failure
        run.status = "ERROR"
        run.error = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        await update_run(run)


async def _run_test_inner(run: Run, pc: Computer, cfg: Settings) -> None:
    """Inner test execution logic."""
    ACTION_CAP = cfg.action_cap
    actions: list[dict] = []
    saw_task_complete = False
    # Create artifacts directory
    run_dir = Path(f"{cfg.artifacts_dir}/{run.id}")
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Use provided computer instance
    computer = pc

    # Initialize frame counter
    frame_count = 0

    def progress_callback(event_type: str, event_data):
        """
        • Persist screenshots for video (unchanged)
        • Pipe tool_result objects through event_capture.extract_actions()
          so actions[] is filled even when screenshots aren't saved.
        """
        nonlocal frame_count, saw_task_complete, actions   # keep actions list!

        # 1 — task_complete fast-exit
        if event_type == "tool_result" and _contains_task_complete(event_data):
            saw_task_complete = True
            return

        # 2 — harvest actionable events
        if event_type == "tool_result":
            actions.extend(extract_actions(event_data))

            # 3 — save any base64 screenshot found in the same payload
            for block in event_data.get("content", []):
                if block.get("type") == "image":
                    src = block.get("source", {})
                    if src.get("type") == "base64":
                        raw = base64.b64decode(src["data"])
                        ext = guess_ext(raw)
                        (frames_dir / f"frame_{frame_count:04d}.{ext}").write_bytes(raw)
                        frame_count += 1


    # Run the test
    initial_prompt = (
        (run.intent or "") + "\n\n"
        f"Step 1: in Firefox, type **exactly** {run.target_url} in the address bar and press Enter. "
        "Stay on that origin; do not use the toolbar for search.\n\n"
        "When the goal is fully satisfied, call the tool `task_complete()` **once** and stop."
    )

    ### Phase 1 – initial prompt ############################################
    response1 = await asyncio.to_thread(
        computer.prompt,
        initial_prompt,
        model=cfg.claude_model,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        callback=progress_callback,
        thinking_enabled=cfg.thinking_enabled,
    )

    walk_and_save_images(response1, frames_dir, [frame_count])

    # After `_dump_response_images(...)`
    for msg in (response1 if isinstance(response1, list) else []):
        if isinstance(msg, dict) and msg.get("type") == "tool_result":
            actions.extend(extract_actions(msg))

    # --- Evaluate success criteria ---------------------------------------
    if run.outcome is None:             # only if task_complete() didn't decide
        assertions = run.success or []
        # NOTE: replace the next line with a real call if the Orgo SDK grows one
        page_text = computer.page_text() if hasattr(computer, "page_text") else ""
        import re
        failures = [pat for pat in assertions if not re.search(pat, page_text, re.I)]
        run.outcome = "ASSERTION_FAIL" if failures else "SUCCESS"

    # Update frame count
    frame_count = len(list(frames_dir.glob("frame_*.*")))

    # Guard against silent failures
    if frame_count == 0:
        raise RuntimeError("Screenshot stream returned zero frames")

    if len(actions) >= ACTION_CAP:
        run.looped = True
        if run.outcome is None:
            run.outcome = "DESIGN_FAIL"

    # Build video from frames
    try:
        video_path = await asyncio.to_thread(
            build_video, frames_dir, fps=1.0 / run.seconds_per_frame
        )
    except FFmpegFailure as fferr:
        run.status = "ERROR"
        run.error = "FFmpeg error — see log"
        run.log_path = str(fferr.log_path)
        run.finished_at = datetime.now(timezone.utc)
        await update_run(run)
        return

    # Log frame count
    print(f"[run {run.id}] saved {frame_count} frame(s)")

    # Generate all artifacts using unified builder
    run.artifact_files = build_all(run_dir, actions, run.outcome or 'FAILED')

    # Update run with success/failure based on outcome
    run.video_path = str(video_path)
    run.status = "SUCCEEDED" if run.outcome == "SUCCESS" else "FAILED"
    run.finished_at = datetime.now(timezone.utc)
    await update_run(run)
