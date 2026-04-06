---
name: add-bot-adapter
description: Add or update YAML-driven Telegram bot adapters for musigate. Use when an agent needs to probe a new Telegram bot, classify its interaction pattern, implement or revise the adapter with minimal Python changes, and validate that the adapter works both in development and in packaged releases.
---

# Add Bot Adapter

Use this skill when the task is to integrate a Telegram bot into musigate.

## Default approach

1. Probe the real bot first.
2. Prefer a YAML-only adapter.
3. Touch Python only when the bot truly introduces a new response shape, selection rule, or CLI need.
4. If the adapter should ship in releases, keep the packaged copy aligned.

Load [references/adapter-workflow.md](references/adapter-workflow.md) for the exact mapping from observed bot behavior to current musigate primitives.

## Workflow

### 1. Probe the bot

- Start with [tmp_probe_bot.py](../../tmp_probe_bot.py).
- Probe at least these inputs when relevant: `/start`, a plain query, `/search <query>`, and a URL.
- Capture `text`, `buttons`, `audio`, `document`, and the ordering of follow-up messages.

### 2. Classify the interaction

Choose the simplest matching pattern:

- Direct query returns an audio file.
- Query returns numbered inline buttons, then clicking one returns audio.
- Query returns text plus buttons; use the text as the displayed result list.
- Query requires replying with a number instead of clicking a button.
- Query branches on returned text or response type.

### 3. Prefer YAML first

- Start from [bots/music163.yaml](../../bots/music163.yaml) or [bots/music_v1.yaml](../../bots/music_v1.yaml).
- Keep `match_text_index` when the bot returns numbered text plus numeric buttons unless the bot clearly needs something else.
- Update the development adapter under [bots](../../bots).
- If the adapter should work from installed wheels, mirror it under [src/musigate/resources/bots](../../src/musigate/resources/bots).

### 4. Touch Python only when necessary

- Edit [src/musigate/telegram/listener.py](../../src/musigate/telegram/listener.py) for new response parsing or metadata extraction.
- Edit [src/musigate/gateway/selector.py](../../src/musigate/gateway/selector.py) for new button selection logic.
- Edit [src/musigate/gateway/executor.py](../../src/musigate/gateway/executor.py) for a new action or context behavior.
- Edit [src/musigate/cli.py](../../src/musigate/cli.py) only for a genuine user-facing flag or output change.

### 5. Validate

- Add or update tests under [tests](../../tests).
- Run `.\.venv\Scripts\python.exe -m pytest -q`.
- Run `test --bot <name>`, then real `search` and `download` commands with the new adapter.
- If the adapter is release-worthy, build a wheel and confirm the packaged adapter resolves outside the repo root.

## Guardrails

- Do not replace a working similarity-based strategy with `first` just to make a probe pass.
- Do not invent a new response type when `inline_buttons`, `text_message`, `audio_file`, or `document` already model the bot correctly.
- Do not forget the packaged resource copy for release-worthy adapters.
