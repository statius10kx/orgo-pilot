"""OrgoLab main entry point."""

import uvicorn


def main():
    """Run the OrgoLab server."""
    uvicorn.run(
        "orgolab.api:app",
        host="0.0.0.0",
        port=8000
    )


if __name__ == "__main__":
    main()
