"""Step 2 — Give the tutor file tools and streaming.

New concepts vs Step 1:
- allowed_tools + permission_mode='acceptEdits': writes files without prompting you for approval
- cwd: scopes the agent's file access to data/ next to this script
- setting_sources=[]: isolates from your local Claude Code config
- model='sonnet' + effort='low': fast conversational replies
- include_partial_messages=True + StreamEvent: token-by-token output

Each query() call is a fresh session — the tutor's memory lives in the files it writes,
not in chat history. It reads its own notes at the start of each turn to recall context.
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
Keep replies short, warm and conversational. Start simple and stretch the learner only a little at a time.

You keep your memory of the learner as files. Read any that exist to recall who you're talking to,
and after each exchange update them silently — never mention or narrate the file work.
Always use these exact absolute paths:
- {_D}/vocab.json    {{"words": [{{"es": "...", "en": "...", "confidence": 0-5, "count": <times used>}}]}}
- {_D}/grammar.json  {{"topics": [{{"topic": "...", "status": "introduced|practising|comfortable", "note": "..."}}]}}
- {_D}/mistakes.json {{"mistakes": [{{"error": "...", "correction": "...", "note": "..."}}]}}
- {_D}/notes_about_student.md      — name, interests, goals
- {_D}/learning_journey_phases.md  — your phased learning plan"""

options = ClaudeAgentOptions(
    system_prompt=TUTOR_PROMPT,
    model="sonnet",
    effort="low",
    include_partial_messages=True,
    allowed_tools=["Read", "Write", "Edit"],
    permission_mode="acceptEdits",
    cwd=str(DATA.resolve()),
    setting_sources=[],
)


async def chat(prompt: str) -> None:
    async for message in query(prompt=prompt, options=options):
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


async def main():
    print(f"{LANGUAGE} Tutor — memory stored in {DATA} (type 'quit' to exit)\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if user_input:
            print("Tutor: ", end="", flush=True)
            await chat(user_input)


asyncio.run(main())
