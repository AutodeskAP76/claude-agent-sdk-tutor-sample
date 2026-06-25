# Language Tutor using the Claude Agent SDK

A conversational language tutor built on the [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview). The project is organized as four progressive steps, each introducing one new SDK capability.

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

## Steps

| Folder | What's new |
|---|---|
| `step1/` | Bare `query()` loop — a model with a persona, ~15 lines |
| `step2/` | File tools and streaming — the tutor keeps its own notes in `data/` |
| `step3/` | Background specialist agent — a high-effort coach revises the learning plan concurrently |
| `step4/` | Full Gradio app — live XP bar, vocab, grammar and journey panels |

Run any step directly:

```bash
uv run python step1/tutor.py
uv run python step2/tutor.py
uv run python step3/tutor.py
uv run python step4/tutor_app.py
```

Each step creates its own `data/` folder next to the script, so learner progress is scoped to each step.

## Authentication

An API key isn't needed. The SDK uses your **Claude Code subscription login** — you're set if you already use Claude Code (on a fresh machine, run `claude setup-token` once). Just make sure `ANTHROPIC_API_KEY` is *not* set, or it would bill the API instead of your subscription.
