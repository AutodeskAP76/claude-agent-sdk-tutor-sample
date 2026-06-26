FROM python:3.12-slim

WORKDIR /app

# Install uv package manager
RUN pip install uv --quiet

# Copy dependency files first — Docker caches this layer and only re-runs
# uv sync when pyproject.toml or uv.lock changes (faster rebuilds)
COPY pyproject.toml uv.lock ./

# Install all Python dependencies.
# This also installs the Linux version of the bundled claude CLI
# (the Windows .exe is not used here — the right binary is chosen at install time)
RUN uv sync --frozen

# Copy only the skills — NOT .claude/settings.json or settings.local.json.
# Those files are written by Claude Code on the developer's machine and contain
# Windows absolute paths that break on Linux inside the container.
COPY .claude/skills/ .claude/skills/

# Copy the step5 application code and static web client
COPY step5/ step5/

# Expose the FastAPI server port
EXPOSE 8000

# Start the API server
CMD ["uv", "run", "python", "step5/run.py"]
