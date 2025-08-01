import asyncio
from typing import Dict, Optional
from uuid import UUID, uuid4

from orgolab.domain.models import Run

runs: Dict[UUID, Run] = {}
_lock = asyncio.Lock()


async def create_run(url: str, *, spf: float = 0.1, **kwargs) -> Run:
    async with _lock:
        run = Run(
            id=uuid4(),
            target_url=url,
            status="PENDING",
            seconds_per_frame=spf,
            intent=kwargs.get("intent"),
            success=kwargs.get("success"),
            context=kwargs.get("context"),
        )
        runs[run.id] = run
        return run


async def get_run(run_id: UUID) -> Optional[Run]:
    # No lock needed for a plain read; dict access is atomic
    # inside a single-threaded asyncio event loop.
    return runs.get(run_id)


async def update_run(run: Run) -> None:
    async with _lock:
        runs[run.id] = run
