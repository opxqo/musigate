---
name: musigate-cli
description: Run, verify, and troubleshoot musigate CLI workflows. Use when an agent needs to log in to Telegram, inspect available bot adapters, search tracks, download by smart match or explicit numbered result, collect JSON output, or debug installed-versus-repo musigate behavior.
---

# Musigate CLI

Use this skill when the task is about operating `musigate`, not changing its internals.

## Default approach

1. In repo development, prefer the repo venv entrypoint for reliability:
   `.\.venv\Scripts\python.exe -m musigate.cli ...`
2. For normal user flows or installed-package validation, use `musigate ...`.
3. Start with `list-bots` before assuming a bot exists.
4. Prefer `--json` when another tool, script, or agent needs stable output.

Load [references/commands.md](references/commands.md) for exact command patterns.

## Login model

- `musigate login` is the normal entrypoint.
- If Telegram credentials are missing, the CLI prompts for them and saves them to `~/.musigate/.env` by default.
- Sessions also live under `~/.musigate` by default.
- `MUSIGATE_HOME` overrides that location.
- If Telegram commands fail before connecting, check `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, proxy settings, and whether the session path is the one the user expects.

## Common workflow

### 1. Verify environment

- Run `list-bots`.
- If the user sees `ModuleNotFoundError: No module named 'musigate'`, switch to the repo venv or use the installed command instead of `python -m musigate.cli` from a random directory.
- If runtime behavior differs between repo and installed package, compare [src/musigate/resources/bots](../../../src/musigate/resources/bots) with development adapters under [bots](../../../bots).

### 2. Search

- Use `search "<query>" --bot <bot>` for human-readable output.
- Use `search "<query>" --bot <bot> --json` for parsed `results` plus `raw_text`.
- Treat the numbered search output as the source of truth for later `--pick` values.

### 3. Download

- Use `download "<query>" --bot <bot>` for adapter-defined smart matching.
- Use `download "<query>" --bot <bot> --pick <n>` to force a specific numbered search result.
- Use `--output <dir>` to override the target directory.
- Expect normal downloads to print progress, speed, and ETA.
- Expect `--json` downloads to suppress progress logs and return a structured payload instead.

### 4. Troubleshoot

- Inspect [src/musigate/cli.py](../../../src/musigate/cli.py) for command flags and JSON payload shape.
- Inspect [src/musigate/telegram/listener.py](../../../src/musigate/telegram/listener.py) when response parsing, metadata extraction, or numbered search rendering looks wrong.
- Inspect [src/musigate/utils/downloader.py](../../../src/musigate/utils/downloader.py) when progress output or completion behavior looks wrong.
- Inspect [src/musigate/utils/config.py](../../../src/musigate/utils/config.py) when `.env`, session, or `MUSIGATE_HOME` behavior is involved.

## Validation

- Run `.\.venv\Scripts\python.exe -m pytest -q` after CLI-facing changes.
- Smoke-test `login`, `list-bots`, `search`, and at least one `download` path when touching runtime behavior.
- When validating releases, build a wheel and test from outside the repo root.
