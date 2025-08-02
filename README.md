**Orgo Pilot**

Orgo Pilot turns a URL, intent and optional further context into a fully recorded browser session and a set of ready-to-share artifacts.

---

### How a run works

1. **Kick-off**
   POST to `/runs` (or click **Start Run**) with:

   * `url` — the page to open
   * `intent` — free-text goal
   * `seconds_per_frame` — screenshot cadence
   * `context` — JSON blob passed straight to the agent (optional)

2. **Execution**
   The executor injects a system prompt that tells the Orgo LLM to open the URL, stay on the same origin, and stop when it’s done. It streams every `tool_result` event in real time.

3. **Guard-rails**

   * Hard timeout (`MAX_RUN_SECONDS`, default 180 s)
   * Step cap of 40; if that limit is hit first, the run is marked **DESIGN\_FAIL**

4. **Completion**
   When the session ends, the in-memory store sets the status to **SUCCEEDED** or **FAILED** and records the outcome (`SUCCESS` or `DESIGN_FAIL`).

---

### Artifacts produced

* `video.mp4` — the full screen recording stitched from every captured frame
* `actions.json` — an ordered log of clicks, key-presses, scrolls, and other UI events, including selectors or coordinates when available
* `orgo_replay.py` — a standalone script that replays the flow through the Orgo SDK without using any LLM credits
* `ffmpeg.log` — only present if FFmpeg errors while building the video

All files are placed under `/artifacts/<run-id>/`.

---

### Dashboard flow

The web UI shows live status transitions (**PENDING → RUNNING → SUCCEEDED / FAILED**). When a run finishes, the video and download links appear immediately. Review the footage, optionally hit **Accept Run** to tag it as good, and share the artifacts with your team. That’s the entire current feature set—record a flow, guard it, and hand back a video plus a replay script.



## Project Structure

```
orgo_scaffod/
├── src/                           # Source code
│   ├── orgolab/                   # Main application package
│   │   ├── __init__.py
│   │   ├── api/                   # FastAPI web application
│   │   │   ├── __init__.py
│   │   │   ├── app.py             # FastAPI app instance
│   │   │   ├── routes.py          # API endpoints
│   │   │   └── lifespan.py        # App lifecycle management
│   │   ├── core/                  # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── executor.py        # Orgo test runner
│   │   │   ├── action_log.py      # Action logging utilities
│   │   │   ├── event_capture.py   # Event extraction from Orgo
│   │   │   ├── images.py          # Image processing utilities
│   │   │   ├── artifacts/         # Artifact generation
│   │   │   │   └── __init__.py    # Unified artifact builder
│   │   │   └── replay/            # Replay script generators
│   │   │       ├── __init__.py
│   │   │       ├── orgo.py        # Orgo replay script generator
│   │   │       └── sandbox.py     # HTML sandbox snippet generator
│   │   ├── domain/                # Domain models and config
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # Pydantic data models
│   │   │   ├── config.py          # Configuration management
│   │   │   └── constants.py       # Application constants
│   │   ├── infra/                 # Infrastructure layer
│   │   │   ├── __init__.py
│   │   │   ├── store.py           # In-memory data store
│   │   │   ├── artifacts.py       # Video generation from screenshots
│   │   │   └── ffmpeg.py          # FFmpeg utility functions
│   │   └── web/                   # Web UI
│   │       └── index.html         # Dashboard interface
├── .env.example                   # Environment variables template
├── pyproject.toml                 # Project metadata and tool config
└── README.md
```

## Installation

1. Clone the repository:


2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Orgo and Anthropic API keys
```

## Quick Start (Local)

1. Start the web server:
```bash
python -m orgolab
# Or use the installed command:
orgolab
```

2. Open the dashboard:
```
http://localhost:8000
```

3. Submit a test with:
   - **URL**: Target website to test (Claude will navigate directly to this URL)
   - **Intent**: What the test should do (e.g., "sign up and reach dashboard")
   - **Context**: Optional JSON data for the test (e.g., credentials)

### API Usage (cURL / Postman)

```bash
# 1 — Kick off a test run
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
        "url": "https://example.com",
        "intent": "sign up and reach dashboard",
        "seconds_per_frame": 0.10,
        "context": {}
      }'

# Response → {"id": "<uuid>", "status": "PENDING", ...}

# 2 — Poll until the run finishes
curl http://localhost:8000/runs/<uuid>
# Returns: status, outcome, and artifacts array

# 3 — (Optional) Accept a successful run
curl -X POST http://localhost:8000/runs/<uuid>/accept
```

<details><summary>Postman Collection (import JSON)</summary>

```json
{
  "info": { "name": "OrgoLab API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json" },
  "item": [
    {
      "name": "Create Run",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": { "raw": "http://localhost:8000/runs" },
        "body": { "mode": "raw", "raw": "{\n  \"url\": \"https://example.com\",\n  \"intent\": \"sign up and reach dashboard\",\n  \"seconds_per_frame\": 0.10,\n  \"context\": {}\n}" }
      }
    },
    {
      "name": "Get Run Status",
      "request": { "method": "GET", "url": { "raw": "http://localhost:8000/runs/{{run_id}}" } }
    },
    {
      "name": "Accept Run",
      "request": { "method": "POST", "url": { "raw": "http://localhost:8000/runs/{{run_id}}/accept" } }
    }
  ]
}
```
</details>

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude
- `ORGO_PROJECT_ID`: Your Orgo project ID
- `ORGO_API_KEY`: Your Orgo API key
- `MAX_RUN_SECONDS`: Maximum execution time per test (default: 180)

## Development

### Code Quality

The project uses:
- **Black** for code formatting
- **Ruff** for linting

Install development dependencies:
```bash
pip install -e ".[dev]"
```

### API Documentation

Once the server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Artifacts Generated

Each test run produces the following artifacts:

| File | Description |
|------|-------------|
| `video.mp4` | Screen recording of the test execution |
| `actions.json` | Log of all actions performed during the test |
| `orgo_replay.py` | Python script to replay the test using Orgo API |
| `sandbox_snippet.html` | Interactive HTML snippet for browser-based replay |

## Test Outcomes

- **SUCCESS**: Test completed successfully (Claude called task_complete())
- **DESIGN_FAIL**: Test exceeded maximum steps (40) without completing

## Key Findings

The Orgo API delivers screenshot data through the prompt's return value, not via callbacks. The executor has been updated to extract screenshots from both sources for maximum compatibility.

## License

MIT License - see LICENSE file for details.
