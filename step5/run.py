"""Launcher for the Step 5 tutor API.

Why this file exists:
The claude_agent_sdk spawns the bundled CLI as a subprocess via asyncio.create_subprocess_exec.
On Windows, the default SelectorEventLoop does NOT support subprocesses — only the
ProactorEventLoop does. The fix must happen BEFORE uvicorn.run() calls asyncio.run(),
because asyncio.run() creates a new event loop from the current policy. Setting the policy
inside tutor_api.py comes too late (the loop is already running when the module is imported).

Setting it here — before uvicorn.run() — ensures asyncio.run() creates a ProactorEventLoop.

The project root is added to sys.path so that 'step5' is importable regardless of how
this script is invoked (e.g. `python step5/run.py` only adds step5/ to sys.path, not root).
"""
import sys
import asyncio
from pathlib import Path

# Ensure the project root is on sys.path so 'step5' is importable.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn
from step5.tutor_api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
