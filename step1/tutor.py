"""Step 1 — The simplest possible agent loop.

query() IS the loop: it handles tool calls, retries, and context internally.
No tools, no streaming, no session state — just a model with a persona.
"""
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

LANGUAGE = "Spanish"

options = ClaudeAgentOptions(
    system_prompt=f"You are speaking with a beginner at {LANGUAGE} and having a friendly conversation to help them learn.",
)


async def main():
    async for message in query(prompt="Hola!", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


asyncio.run(main())
