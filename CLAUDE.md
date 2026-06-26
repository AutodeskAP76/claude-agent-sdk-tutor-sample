# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (requires uv)
uv sync

# Run any step
uv run python step1/tutor.py
uv run python step2/tutor.py
uv run python step3/tutor.py
uv run python step4/tutor_app.py
uv run python step5/run.py

# First-time auth on a fresh machine (no API key needed — uses Claude Code subscription)
claude setup-token
```

## Structure

Five progressive steps, each a self-contained runnable script:

| Folder | What's new | Entry point |
|---|---|---|
| `step1/` | Bare `query()` loop, single turn | `tutor.py` |
| `step2/` | File tools + streaming, interactive REPL | `tutor.py` |
| `step3/` | Background coach via `asyncio.create_task()` | `tutor.py` |
| `step4/` | Full Gradio app, session resumption, scribe agent | `tutor_app.py` |
| `step5/` | FastAPI web service, per-user TutorSession, SSE streaming, vanilla JS client | `tutor_api.py` |

Each step creates its own `data/` subfolder (gitignored) for learner state.

## Architecture

### Three-agent design (Step 4)

The core insight: **the conversational tutor has no tools**. Instead of letting it read/write files mid-chat (which would slow replies), it receives a pre-built `learner_brief()` injected into its system prompt at the start of each turn. All bookkeeping is delegated to two background agents:

| Agent | Purpose | `effort` | Runs |
|---|---|---|---|
| **Tutor** | Conversation only | `low` | Foreground, streamed |
| **Scribe** | Updates `vocab.json`, `grammar.json`, `mistakes.json`, `notes_about_student.md` | `low` | Background `asyncio` task after every turn |
| **Coach** | Rewrites `learning_journey_phases.md` | `high` | Background every `REFINE_EVERY=3` turns |

### Step progression

- **Step 1→2**: add `allowed_tools`, `permission_mode`, `cwd`, `setting_sources=[]`, streaming
- **Step 2→3**: add a second agent (`coach_options`) launched as `asyncio.create_task()`; the tutor still owns its own files
- **Step 3→4**: the tutor loses its tools entirely; a dedicated scribe takes over file writes; session continuity via `resume=session_id`; Gradio UI polls `data/` on a `gr.Timer(2.0)` to live-refresh panels
- **Step 4→5**: three major upgrades — (1) **web-based**: Gradio replaced by a FastAPI service + vanilla JS client accessible from any browser; (2) **multi-user sessions**: `TutorSession` class encapsulates all per-user state, replacing module-level globals — each user gets an isolated in-memory session keyed by a UUID; (3) **session-scoped memory**: all data files (`vocab.json`, `grammar.json`, etc.) are written under `data/<session_id>/` so every learner's history is fully isolated and persists across browser refreshes via `localStorage`

### Session continuity (Step 4)

Multi-turn chat is maintained via `resume=session_id` in `ClaudeAgentOptions`. The `session_id` comes from `SystemMessage(subtype="init")` on the first turn and is threaded through `gr.State` in the UI.

### XP

Computed as a view over scribe-tracked data — `confidence × 10 + count` per vocab word — not a separately tracked value.

### Multi-user isolation (Step 5)

Each browser session is fully isolated. On first visit the client calls `POST /session` with no `user_id`, receives a fresh UUID, and stores it in `localStorage`. Subsequent visits reuse the same UUID, resuming the existing session. Different browsers (or private/incognito windows) have separate `localStorage`, so each gets its own UUID and therefore its own session.

Storage is per-session: `TutorSession` writes all data files under `step5/data/<session_id>/`, so scribe and coach agents for concurrent sessions never share or overwrite each other's files.

### Auth

No `ANTHROPIC_API_KEY` should be set. The SDK drives the `claude` CLI using the user's Claude Code subscription login. If the env var is set, it bills the API instead.
