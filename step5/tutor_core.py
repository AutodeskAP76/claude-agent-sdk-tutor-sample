"""Step 5 — TutorSession: per-user isolated agent engine for web service deployment.

New concepts vs Step 4:
- TutorSession class encapsulates all per-user state (no module-level globals)
- data_dir is passed at construction time, enabling one session per user
- stream_reply() yields raw text chunks (deltas), not accumulated text
- Absolute paths in scribe/coach prompts (Windows cwd fix)
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
REFINE_EVERY = 3


class TutorSession:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._session_id = None
        self._scribe_task = None
        self._coach_task = None
        self._turns_since_refine = 0

        _d = self.data_dir.resolve().as_posix()

        self._tutor_prompt = f"""You are a warm, patient {LANGUAGE} tutor having a relaxed, friendly conversation with a beginner.
Speak mostly in {LANGUAGE}, adding short English glosses for anything new so the learner is never lost.
Keep replies short, warm and conversational. Start simple and stretch the learner only a little at a time.
Gently correct meaningful mistakes in passing, without breaking the flow. Because this is an interactive chat, don't fuss over small details like accents or punctuation -- at most mention them lightly in passing, and save that precision for later stages as the learner advances."""

        self._chat_options = ClaudeAgentOptions(
            system_prompt=self._tutor_prompt,
            model="sonnet",
            effort="low",
            cwd=str(self.data_dir.resolve()),
            setting_sources=[],
        )

        self._scribe_options = ClaudeAgentOptions(
            system_prompt=f"""You quietly keep a {LANGUAGE} learner's progress files up to date from the latest exchange.
Always use these exact absolute paths:
- {_d}/vocab.json    {{"words": [{{"es": "...", "en": "...", "confidence": 0-5, "count": <times used>}}]}}  -- add words the learner used or met; bump count; raise confidence as they show mastery
- {_d}/grammar.json  {{"topics": [{{"topic": "...", "status": "introduced|practising|comfortable", "note": "..."}}]}}
- {_d}/mistakes.json {{"mistakes": [{{"error": "...", "correction": "...", "note": "..."}}]}}  -- only meaningful mistakes; ignore accent and punctuation slips at this stage
- {_d}/notes_about_student.md  -- name, interests, goals
Read each file, then edit it in place. Be quick and surgical. Do not touch {_d}/learning_journey_phases.md (another agent owns it).""",
            model="sonnet",
            effort="low",
            allowed_tools=["Read", "Write", "Edit"],
            permission_mode="acceptEdits",
            cwd=str(self.data_dir.resolve()),
            setting_sources=[],
        )

        self._coach_options = ClaudeAgentOptions(
            system_prompt=f"""You are a {LANGUAGE} curriculum coach working quietly behind the scenes.
Read the learner's files using these exact absolute paths: {_d}/vocab.json, {_d}/grammar.json,
{_d}/mistakes.json, {_d}/notes_about_student.md, and {_d}/learning_journey_phases.md.
Then rewrite {_d}/learning_journey_phases.md as a short, gently progressive plan in numbered
phases — each with a focus, a few target words/structures, and a 'ready when' note — tuned
to the learner's recent mistakes and current level. Keep it encouraging and realistic. Work silently.""",
            model="sonnet",
            effort="high",
            allowed_tools=["Read", "Write", "Edit"],
            permission_mode="acceptEdits",
            cwd=str(self.data_dir.resolve()),
            setting_sources=[],
        )

    def learner_brief(self) -> str:
        """Read data files in Python and inline them as text appended to the tutor's system prompt each turn."""
        level, total, _ = self.xp_stats()
        words = ", ".join(w.get("es", "") for w in self.recent_vocab(20)) or "none yet"
        notes = self._read("notes_about_student.md")[:800]
        journey = self._read("learning_journey_phases.md")[:1000]
        return (
            "\n\n--- What you already know about this learner (your memory; never mention these notes) ---\n"
            f"Level ~{level} ({total} XP). Recent vocabulary: {words}.\n"
            f"Notes: {notes}\n"
            f"Current learning plan:\n{journey}"
        )

    async def stream_reply(self, user_msg: str):
        """Stream the tutor's reply, yielding raw text chunks (deltas)."""
        turn = replace(
            self._chat_options,
            system_prompt=self._tutor_prompt + self.learner_brief(),
            include_partial_messages=True,
            resume=self._session_id,
        )
        async for message in query(prompt=user_msg, options=turn):
            if isinstance(message, SystemMessage) and message.subtype == "init":
                self._session_id = message.data.get("session_id", self._session_id)
            elif isinstance(message, StreamEvent):
                ev = message.event
                if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                    yield ev["delta"]["text"]
            elif isinstance(message, ResultMessage):
                self._session_id = message.session_id or self._session_id

    def record_exchange(self, user_msg: str, reply: str) -> None:
        """Background: update vocab/grammar/mistakes/notes from the latest exchange (one at a time)."""
        if self._scribe_task is None or self._scribe_task.done():
            prompt = f"Learner said: {user_msg}\nTutor replied: {reply}\n\nUpdate the memory files accordingly."
            self._scribe_task = asyncio.create_task(self._run(self._scribe_options, prompt))

    def maybe_refine(self) -> None:
        """Background: refine the learning journey at high effort -- only every REFINE_EVERY messages, one at a time."""
        self._turns_since_refine += 1
        if self._turns_since_refine < REFINE_EVERY:
            return
        if self._coach_task is not None and not self._coach_task.done():
            return
        self._turns_since_refine = 0
        self._coach_task = asyncio.create_task(
            self._run(self._coach_options, "Review the learner's progress and refine learning_journey_phases.md.")
        )

    async def _run(self, opts, prompt) -> None:
        """Drive a fire-and-forget agent to completion; we care about its file side-effects, not its output."""
        async for _ in query(prompt=prompt, options=opts):
            pass

    def _read(self, name: str) -> str:
        """Read a file from data_dir, returning empty string if it doesn't exist yet."""
        p = self.data_dir / name
        return p.read_text() if p.exists() else ""

    def _items(self, name: str, key: str) -> list:
        """Load a list from a data file, tolerant of dict-wrapped or bare-list shapes."""
        p = self.data_dir / name
        if not p.exists():
            return []
        data = json.loads(p.read_text())
        if isinstance(data, dict):
            data = data.get(key) or next((v for v in data.values() if isinstance(v, list)), [])
        return data if isinstance(data, list) else []

    def recent_vocab(self, n: int = 10) -> list:
        """The n most recently added words, newest first."""
        return list(reversed(self._items("vocab.json", "words")[-n:]))

    def grammar_topics(self) -> list:
        """All grammar topics tracked so far, in insertion order."""
        return self._items("grammar.json", "topics")

    def journey_text(self) -> str:
        """Raw markdown of the coach-maintained learning plan, empty until the coach has run once."""
        return self._read("learning_journey_phases.md")

    def xp_stats(self) -> tuple:
        """XP is a view over what the agent tracks: confidence × 10 + count per word."""
        words = self._items("vocab.json", "words")
        total = sum(int(w.get("confidence", 1) or 1) * 10 + int(w.get("count", 1) or 1) for w in words)
        return total // 100 + 1, total, total % 100
