"""Agent + data layer for the language tutor -- the engine, no UI.

The tutor IS the agent loop. To keep the chat snappy, the conversational tutor
carries NO tools: we feed it a compact brief of what it already knows, and it just
talks. All bookkeeping happens off to the side in background agents -- a fast scribe
that records vocab/grammar/mistakes/notes, and a high-effort coach that refines the
learning journey -- so the conversation never waits on file I/O.
"""
import asyncio
import json
from dataclasses import replace
from pathlib import Path

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    SystemMessage,
    StreamEvent,
    ResultMessage,
)

LANGUAGE = "Spanish"
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)


# --- the conversational tutor: fast, no tools; we hand it the learner's state ---

TUTOR_PROMPT = f"""You are a warm, patient {LANGUAGE} tutor having a relaxed, friendly conversation with a beginner.
Speak mostly in {LANGUAGE}, adding short English glosses for anything new so the learner is never lost.
Keep replies short, warm and conversational. Start simple and stretch the learner only a little at a time.
Gently correct meaningful mistakes in passing, without breaking the flow. Because this is an interactive chat, don't fuss over small details like accents or punctuation -- at most mention them lightly in passing, and save that precision for later stages as the learner advances."""

chat_options = ClaudeAgentOptions(
    system_prompt=TUTOR_PROMPT,
    model="sonnet",
    effort="low",
    cwd=str(DATA.resolve()),
    setting_sources=[],
)


def learner_brief():
    """A compact snapshot of the learner, fed to the tutor so it never reads files mid-chat."""
    level, total, _ = xp_stats()
    words = ", ".join(w.get("es", "") for w in recent_vocab(20)) or "none yet"
    notes = _read("notes_about_student.md")[:800]
    journey = _read("learning_journey_phases.md")[:1000]
    return (
        "\n\n--- What you already know about this learner (your memory; never mention these notes) ---\n"
        f"Level ~{level} ({total} XP). Recent vocabulary: {words}.\n"
        f"Notes: {notes}\n"
        f"Current learning plan:\n{journey}"
    )


async def stream_reply(user_msg, session_id):
    """Stream the tutor's reply, yielding (accumulated_text, session_id) as it grows."""
    turn = replace(
        chat_options,
        system_prompt=TUTOR_PROMPT + learner_brief(),
        include_partial_messages=True,
        resume=session_id,
    )
    reply, sid = "", session_id
    async for message in query(prompt=user_msg, options=turn):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            sid = message.data.get("session_id", sid)
        elif isinstance(message, StreamEvent):
            ev = message.event
            if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                reply += ev["delta"]["text"]
                yield reply, sid
        elif isinstance(message, ResultMessage):
            sid = message.session_id or sid
    yield reply, sid


# --- background workers: keep the chat light, do bookkeeping off to the side ---

SCRIBE_PROMPT = f"""You quietly keep a {LANGUAGE} learner's progress files up to date from the latest exchange.
Work ONLY with these files, exactly as named, directly in your current working directory. Never create a subfolder and never use a path -- just the bare filenames:
- vocab.json    {{"words": [{{"es": "...", "en": "...", "confidence": 0-5, "count": <times used>}}]}}  -- add words the learner used or met; bump count; raise confidence as they show mastery
- grammar.json  {{"topics": [{{"topic": "...", "status": "introduced|practising|comfortable", "note": "..."}}]}}
- mistakes.json {{"mistakes": [{{"error": "...", "correction": "...", "note": "..."}}]}}  -- only meaningful mistakes; ignore accent and punctuation slips at this stage
- notes_about_student.md  -- name, interests, goals
Read each file, then edit it in place. Be quick and surgical. Do not touch learning_journey_phases.md (another agent owns it)."""

scribe_options = ClaudeAgentOptions(
    system_prompt=SCRIBE_PROMPT,
    model="sonnet",
    effort="low",
    allowed_tools=["Read", "Write", "Edit"],
    permission_mode="acceptEdits",
    cwd=str(DATA.resolve()),
    setting_sources=[],
)

COACH_PROMPT = f"""You are a {LANGUAGE} curriculum coach working quietly behind the scenes.
Read the learner's files: vocab.json, grammar.json, mistakes.json, notes_about_student.md, and the current learning_journey_phases.md.
Then rewrite learning_journey_phases.md as a short, gently progressive plan in numbered phases -- each with a focus, a few target
words/structures, and a 'ready when' note -- tuned to the learner's recent mistakes and current level. Keep it encouraging and
realistic. Work silently and just update the file."""

coach_options = ClaudeAgentOptions(
    system_prompt=COACH_PROMPT,
    model="sonnet",
    effort="high",
    allowed_tools=["Read", "Write", "Edit"],
    permission_mode="acceptEdits",
    cwd=str(DATA.resolve()),
    setting_sources=[],
)

_scribe_task = None
_coach_task = None
_turns_since_refine = 0
REFINE_EVERY = 3  # rewrite the learning journey every N messages, not after every one


def record_exchange(user_msg, reply):
    """Background: update vocab/grammar/mistakes/notes from the latest exchange (one at a time)."""
    global _scribe_task
    if _scribe_task is None or _scribe_task.done():
        prompt = f"Learner said: {user_msg}\nTutor replied: {reply}\n\nUpdate the memory files accordingly."
        _scribe_task = asyncio.create_task(_run(scribe_options, prompt))


def maybe_refine():
    """Background: refine the learning journey at high effort -- only every REFINE_EVERY messages, one at a time."""
    global _coach_task, _turns_since_refine
    _turns_since_refine += 1
    if _turns_since_refine < REFINE_EVERY:
        return
    if _coach_task is not None and not _coach_task.done():
        return  # a refine is still running; keep the count and try again next message
    _turns_since_refine = 0
    _coach_task = asyncio.create_task(
        _run(coach_options, "Review the learner's progress and refine learning_journey_phases.md.")
    )


async def _run(opts, prompt):
    async for _ in query(prompt=prompt, options=opts):
        pass


# --- data readers (the UI renders straight from these) ---

def _read(name):
    p = DATA / name
    return p.read_text() if p.exists() else ""


def _items(name, key):
    """Load a list from a data file, tolerant of dict-wrapped or bare-list shapes."""
    p = DATA / name
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    if isinstance(data, dict):
        data = data.get(key) or next((v for v in data.values() if isinstance(v, list)), [])
    return data if isinstance(data, list) else []


def recent_vocab(n=10):
    """The n most recently added words, newest first."""
    return list(reversed(_items("vocab.json", "words")[-n:]))


def grammar_topics():
    return _items("grammar.json", "topics")


def journey_text():
    return _read("learning_journey_phases.md")


def xp_stats():
    """XP is a view over what the agent tracks: confidence x 10 + count per word."""
    words = _items("vocab.json", "words")
    total = sum(int(w.get("confidence", 1) or 1) * 10 + int(w.get("count", 1) or 1) for w in words)
    return total // 100 + 1, total, total % 100
