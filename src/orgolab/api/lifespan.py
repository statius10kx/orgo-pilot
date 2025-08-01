import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from orgo import Computer

from orgolab.domain.config import Settings

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create artifacts directory
    os.makedirs("artifacts", exist_ok=True)

    # Load settings
    settings = Settings()

    # Initialize Computer instance
    computer = Computer(
        project_id=settings.orgo_project_id,
        api_key=settings.orgo_api_key,
    )

    # Store in app state
    app.state.settings = settings
    app.state.computer = computer

    yield
