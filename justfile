set shell := ["bash", "-euo", "pipefail", "-c"]

default: build

# Sync deps and render every scene (last-frame PNG + low-res video) into out/
# and media/; outputs are validated for transparency and content.
build:
    uv sync
    uv run python scripts/render.py

# Render, then lint and run the test suite.
test: build
    uv run ruff check .
    uv run pytest

# Demos repo — no binary, no launcher (ADR-749: nothing to install).
install:
    @echo "manim-demos: demos repo, nothing to install"
