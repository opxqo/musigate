---
name: add-bot-adapter
description: Add or update YAML-driven Telegram bot adapters for musigate. Use when an agent needs to probe a new Telegram bot, classify its interaction pattern, implement a new adapter mostly in YAML, decide whether core Python changes are actually necessary, and validate search or download behavior before release.
---

# Add Bot Adapter

## Overview

Use this skill to integrate a new Telegram bot into musigate with the least invasive change set possible.

Prefer a YAML-only adapter first. Change Python code only when the bot introduces a genuinely new response type, selection strategy, or user-facing CLI need.

## Workflow

### 1. Probe the bot

- Start with [tmp_probe_bot.py](../../tmp_probe_bot.py).
- Probe at least four inputs when relevant: `/start`, a plain query, `/search <query>`, and a URL.
- Capture `text`, `buttons`, `audio`, `document`, and the ordering of follow-up messages.

### 2. Classify the interaction

Choose the simplest matching pattern:

- Direct query returns an audio file.
- Query returns numbered inline buttons, then clicking one returns audio.
- Query returns text plus buttons; use the text as the result list.
- Query requires replying with a number instead of clicking a button.
- Query has multiple branches depending on returned content.

Load [references/adapter-workflow.md](references/adapter-workflow.md) when you need the canonical mapping to current code.

### 3. Prefer YAML first

- Start from [bots/music163.yaml](../../bots/music163.yaml) or [bots/music_v1.yaml](../../bots/music_v1.yaml).
- Keep `match_text_index` for numbered text plus numeric buttons unless the bot clearly requires a different strategy.
- Add or update the development adapter under [bots](../../bots).
- If the adapter should ship in released wheels, mirror it under [src/musigate/resources/bots](../../src/musigate/resources/bots).

### 4. Touch Python only when necessary

- Edit [src/musigate/telegram/listener.py](../../src/musigate/telegram/listener.py) for new response parsing or metadata extraction.
- Edit [src/musigate/gateway/selector.py](../../src/musigate/gateway/selector.py) for new button selection logic.
- Edit [src/musigate/gateway/executor.py](../../src/musigate/gateway/executor.py) for a new action or context behavior.
- Edit [src/musigate/cli.py](../../src/musigate/cli.py) only for new user-facing flags or output formats.

### 5. Validate

- Add or update tests under [tests](../../tests).
- Run `.\.venv\Scripts\python.exe -m pytest -q`.
- Run `test --bot <name>`, then real `search` and `download` commands with the new adapter.
- If the adapter is intended for release, build a wheel and confirm the packaged adapter resolves outside the repo root.

## Guardrails

- Do not replace a working similarity-based strategy with `first` just to make a probe pass.
- Do not add a new response type when the existing `inline_buttons` or `audio_file` structures already model the bot correctly.
- Do not forget the packaged resource copy for release-worthy adapters.
