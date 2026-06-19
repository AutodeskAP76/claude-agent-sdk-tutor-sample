# Language Tutor using the Claude Agent SDK

A conversational language tutor built on the [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview). The notebook starts as a simple agent loop and progresses to a small Gradio app with a live vocabulary, grammar, an XP bar and a self-updating learning journey.

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/ed-donner/tutor.git
   cd tutor
   ```
2. **Install [uv](https://docs.astral.sh/uv/)** if you don't already have it
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Install dependencies**
   ```bash
   uv sync
   ```
4. **Open `tutor.ipynb`** in VS Code, Cursor, or Jupyter.
5. **Select the kernel** — choose this project's `.venv` (uv) environment, then run the cells top to bottom. The final step launches the Gradio app locally.

## Authentication

An API key isn't needed. The SDK uses your **Claude Code subscription login** — you're set if you already use Claude Code (on a fresh machine, run `claude setup-token` once). Just make sure `ANTHROPIC_API_KEY` is *not* set, or it would bill the API instead of your subscription.
