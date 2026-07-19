# Project Agent Instructions

## Working Style

- Use parallel work only for genuinely independent tasks that materially reduce total time.
- Keep context gathering bounded to the files and symbols required for the current decision.
- Delegate only when a specialist or a truly independent research lane adds clear value.
- Prefer direct, focused validation before launching broader investigation.
- Keep background-agent batches small and avoid duplicate research lanes.
- Do not wait indefinitely for background work. If it exceeds its useful time budget, cancel it and continue with the best verified evidence available.
- Do not replace a slow background task with multiple duplicate tasks.
- Report blockers promptly instead of silently waiting.

## Focused Validation

Run these commands from `model-server` for game-service changes:

- `uv run ruff check src/game_service tests`
- `uv run basedpyright --level error src/game_service tests`
- `powershell -ExecutionPolicy Bypass -File scripts/test_memory.ps1`
