"""Step 5 — FastAPI web service exposing TutorSession as HTTP endpoints.

New concepts vs Step 4:
- TutorSession instances stored in an in-memory registry keyed by user_id
- SSE (Server-Sent Events) streams the tutor reply token-by-token over HTTP
- Any HTTP client (browser, mobile app, curl) can consume the API
- Gradio dependency dropped entirely

Run:
    uv run uvicorn step5.tutor_api:app --reload

Endpoints:
    POST /session?user_id=<id>   — create or resume a session
    POST /chat/{session_id}      — stream a tutor reply (SSE)
    GET  /panels/{session_id}    — fetch current learner stats as JSON
"""
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from step5.tutor_core import TutorSession

app = FastAPI(title="Language Tutor API")

DATA_ROOT = Path(__file__).parent / "data"
DATA_ROOT.mkdir(exist_ok=True)

# In-memory session registry keyed by user_id.
# Replace with Redis or a DB for multi-process / production deployments.
_sessions: dict[str, TutorSession] = {}


def _get_session(session_id: str) -> TutorSession:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found. Call POST /session first.")
    return _sessions[session_id]


# --- session management ---

class SessionResponse(BaseModel):
    session_id: str


@app.post("/session", response_model=SessionResponse)
async def create_session(user_id: str | None = None):
    """Create or resume a tutor session.

    - First call (no user_id): generates a fresh UUID, creates a new TutorSession with its
      own data directory, and returns the session_id. Store this in the client (e.g. localStorage).
    - Subsequent calls (same user_id): returns the existing session so the learner's history
      and data files are preserved across browser refreshes or reconnects.
    """
    uid = user_id or str(uuid.uuid4())
    if uid not in _sessions:
        _sessions[uid] = TutorSession(data_dir=DATA_ROOT / uid)
    return SessionResponse(session_id=uid)


# --- chat via SSE ---

class ChatRequest(BaseModel):
    message: str


@app.post("/chat/{session_id}")
async def chat(session_id: str, req: ChatRequest):
    """Send a message to the tutor and stream the reply token-by-token via Server-Sent Events.

    The response is a text/event-stream where each line is a JSON-encoded SSE event:
      data: {"type": "chunk", "text": "Hola"}\n\n   — one text token from the tutor
      data: {"type": "done"}\n\n                    — stream finished; background agents fired

    After the stream closes, two background asyncio tasks are fired without blocking the response:
      - record_exchange(): scribe agent updates vocab/grammar/mistakes/notes files
      - maybe_refine():    coach agent rewrites the learning journey every REFINE_EVERY turns

    Chunks are JSON-encoded to safely transport newlines and special characters over SSE.
    The client accumulates chunks and appends them to build the full reply string.
    """
    session = _get_session(session_id)
    chunks: list[str] = []

    async def event_stream():
        async for chunk in session.stream_reply(req.message):
            chunks.append(chunk)
            payload = json.dumps({"type": "chunk", "text": chunk})
            yield f"data: {payload}\n\n"

        reply = "".join(chunks)
        session.record_exchange(req.message, reply)
        session.maybe_refine()
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- panels ---

@app.get("/panels/{session_id}")
async def panels(session_id: str):
    """Return the current learner stats as JSON for the UI side panels.

    Reads directly from the data files written by the scribe and coach background agents.
    The web client polls this endpoint every 2 seconds so the panels update live as agents
    finish writing — no websocket or push needed.

    Response shape:
      {
        "xp":      {"level": int, "total": int, "into": int},   -- into = % progress to next level
        "vocab":   [{"es": str, "en": str, "confidence": int, "count": int}, ...],
        "grammar": [{"topic": str, "status": str, "note": str}, ...],
        "journey": str   -- raw markdown of the coach's learning plan
      }
    """
    session = _get_session(session_id)
    level, total, into = session.xp_stats()
    return {
        "xp": {"level": level, "total": total, "into": into},
        "vocab": session.recent_vocab(10),
        "grammar": session.grammar_topics(),
        "journey": session.journey_text(),
    }


# --- serve the web client ---
# Mount last so API routes take priority.
_static = Path(__file__).parent / "static"
_static.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=_static, html=True), name="static")
