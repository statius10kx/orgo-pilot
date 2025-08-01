from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .lifespan import lifespan
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    # Include API routes
    app.include_router(router)

    # Mount static files to serve artifacts
    app.mount("/artifacts", StaticFiles(directory="artifacts"), name="artifacts")

    # Mount static files for the dashboard
    app.mount("/", StaticFiles(directory="src/orgolab/web", html=True), name="static")

    return app


app = create_app()
