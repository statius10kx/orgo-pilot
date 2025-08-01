from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, HttpUrl

from orgolab.infra.store import create_run as store_create_run
from orgolab.infra.store import get_run, update_run

router = APIRouter()


class RunRequest(BaseModel):
    url: HttpUrl
    intent: str | None = None
    context: dict[str, Any] | None = None
    seconds_per_frame: float = 0.1
    success: list[str] | None = None


@router.post("/runs")
async def create_run(request: RunRequest, background_tasks: BackgroundTasks, req: Request) -> Dict[str, str]:
    """Create a new test run."""
    run = await store_create_run(
        str(request.url),
        spf=request.seconds_per_frame,
        intent=request.intent,
        success=request.success,
        context=request.context,
    )

    # Get settings and computer from app state
    settings = req.app.state.settings
    computer = req.app.state.computer

    # Import here to avoid circular dependency
    from orgolab.core.executor import run_test

    # Schedule the test execution
    background_tasks.add_task(run_test, run, computer, cfg=settings)

    return {"id": str(run.id)}


@router.post("/tests", include_in_schema=False)
async def create_test_compat(request: RunRequest, background_tasks: BackgroundTasks, req: Request) -> Dict[str, str]:
    """Legacy endpoint for compatibility."""
    return await create_run(request, background_tasks, req)


@router.get("/runs/{run_id}")
async def get_run_status(run_id: UUID) -> Dict[str, Any]:
    """Get run status and details."""
    run = await get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    result = run.dict_json()
    if run.log_path:
        result["log_url"] = f"/artifacts/{run.id}/ffmpeg.log"
    result["poll_interval"] = 2
    result["accepted"] = run.accepted
    result["looped"] = run.looped
    result["outcome"] = run.outcome
    result["artifacts"] = run.artifact_files or []
    return result


@router.post("/runs/{run_id}/accept")
async def accept_run(run_id: UUID):
    run = await get_run(run_id)
    if not run:
        raise HTTPException(404)
    run.accepted = True
    await update_run(run)
    return {"accepted": True}
