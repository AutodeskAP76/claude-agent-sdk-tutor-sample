"""Step 3 — Add a background specialist agent (the journey coach).

New concept vs Step 2:
- asyncio.create_task() runs a second agent concurrently with the conversation
- The coach is high-effort (slower, deeper reasoning) and only refines the learning plan
- The tutor never waits for the coach — the chat stays snappy

The tutor still owns its own files here (as in Step 2). The clean separation — a
dedicated scribe agent handles all file writes so the tutor carries no tools at all —
is the key architectural upgrade introduced in Step 4.
"""
import asyncio
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, StreamEvent, ToolUseBlock

LANGUAGE = "Spanish"
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

_D = DATA.resolve().as_posix()
TUTOR_PROMPT = f"""You are a warm, patient {LANGUAGE} tutor having a relaxed, friendly conversation with a beginner.
Speak mostly in {LANGUAGE}, adding short English glosses for anything new so the learner is never lost.
Keep replies short, warm and conversational.

You keep your memory of the learner as files. Read any that exist to recall who you're talking to,
and after each exchange update them silently. Always use these exact absolute paths:
- {_D}/vocab.json    {{"words": [{{"es": "...", "en": "...", "confidence": 0-5, "count": <times used>}}]}}
- {_D}/grammar.json  {{"topics": [{{"topic": "...", "status": "introduced|practising|comfortable", "note": "..."}}]}}
- {_D}/mistakes.json {{"mistakes": [{{"error": "...", "correction": "...", "note": "..."}}]}}
- {_D}/notes_about_student.md — name, interests, goals

Do NOT touch {_D}/learning_journey_phases.md — the coach owns that file."""

tutor_options = ClaudeAgentOptions(
    system_prompt=TUTOR_PROMPT,
    model="sonnet",
    effort="low",
    include_partial_messages=True,
    allowed_tools=["Read", "Write", "Edit"],
    permission_mode="acceptEdits",
    cwd=str(DATA.resolve()),
    setting_sources=[],
)

COACH_PROMPT = f"""You are a {LANGUAGE} curriculum coach working quietly behind the scenes.
Read the learner's files using these exact absolute paths: {_D}/vocab.json, {_D}/grammar.json,
{_D}/mistakes.json, {_D}/notes_about_student.md, and {_D}/learning_journey_phases.md.
Then rewrite {_D}/learning_journey_phases.md as a short, gently progressive plan in numbered
phases — each with a focus, a few target words/structures, and a 'ready when' note — tuned
to the learner's recent mistakes and current level."""

coach_options = ClaudeAgentOptions(
    system_prompt=COACH_PROMPT,
    model="sonnet",
    effort="high",
    allowed_tools=["Read", "Write", "Edit"],
    permission_mode="acceptEdits",
    cwd=str(DATA.resolve()),
    setting_sources=[],
)


async def chat(prompt: str) -> None:
    async for message in query(prompt=prompt, options=tutor_options):
        if isinstance(message, StreamEvent):
            ev = message.event
            if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                print(ev["delta"]["text"], end="", flush=True)
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    name = Path(block.input.get("file_path", "")).name
                    print(f"\n  · {block.name} {name}".rstrip(), flush=True)
    print()

# this is executed on each turn after the tutor's reply, but it runs in the background so the chat never waits on file I/O
# all the logic of this agent is encapsulated in the system prompt, in options specified, and in the prompt provied here every time it is executed
async def run_coach() -> None:
    async for _ in query(
        prompt="Review the learner's progress and refine learning_journey_phases.md.",
        options=coach_options,
    ):
        pass


async def main():
    coach_task = None
    print(f"{LANGUAGE} Tutor with background journey coach (type 'quit' to exit)\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        print("Tutor: ", end="", flush=True)
        await chat(user_input)

        if coach_task is None or coach_task.done():
            coach_task = asyncio.create_task(run_coach())
            print("[Coach revising your learning journey in the background...]")

    if coach_task and not coach_task.done():
        print("[Waiting for coach to finish...]")
        await coach_task


asyncio.run(main())
