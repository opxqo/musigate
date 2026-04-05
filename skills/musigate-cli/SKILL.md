---
name: musigate-cli
description: Operate the musigate command line for login, bot listing, search, download, JSON output, numbered result selection, and smoke tests. Use when an agent needs to run or troubleshoot musigate CLI commands, validate Telegram bot interactions from the terminal, inspect installed bot adapters, or collect machine-readable results for scripts and automation.
---

# Musigate CLI

## Overview

Use this skill to work with the `musigate` CLI from the repository or from an installed wheel.

Prefer the development entrypoint `.\.venv\Scripts\python.exe -m musigate.cli ...` when operating inside the repo. Use the installed `musigate ...` command only when validating packaging or release behavior.

## Quick Start

1. Work from the repository root.
2. Confirm credentials exist in `.env` or environment variables before running login, search, or download flows.
3. List available adapters before assuming a bot exists.
4. Prefer `--json` when another agent or script needs stable structured output.

Load [references/commands.md](references/commands.md) when you need exact command patterns.

## Workflow

### 1. Verify the environment

- Run `.\.venv\Scripts\python.exe -m musigate.cli list-bots` to confirm adapter availability.
- If the user sees `ModuleNotFoundError: No module named 'musigate'`, switch to the project virtualenv or install the package in editable mode.
- If Telegram commands fail early, check `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.

### 2. Search

- Use `search "<query>" --bot <bot>` for human-readable output.
- Use `search "<query>" --bot <bot> --json` when you need `raw_text` and parsed `results`.
- Treat numbered search output as the source of truth for later `--pick` values.

### 3. Download

- Use `download "<query>" --bot <bot>` for smart matching via the configured adapter strategy.
- Use `download "<query>" --bot <bot> --pick <n>` to force an exact numbered result from the search output.
- Use `--output <dir>` to override the target directory.
- Expect human-readable downloads to print progress, speed, and ETA.
- Expect `--json` downloads to suppress progress logs and return a machine-readable payload instead.

### 4. Troubleshoot

- Inspect [src/musigate/cli.py](../../../src/musigate/cli.py) for user-facing options and JSON payload structure.
- Inspect [bots](../../../bots) for development-time bot adapters.
- Inspect [src/musigate/resources/bots](../../../src/musigate/resources/bots) when debugging packaged default adapters.
- Inspect [src/musigate/telegram/listener.py](../../../src/musigate/telegram/listener.py) when search or audio metadata parsing looks wrong.
- Inspect [src/musigate/utils/downloader.py](../../../src/musigate/utils/downloader.py) when progress output or download completion behavior is wrong.

## Validation

- Run `.\.venv\Scripts\python.exe -m pytest -q` after CLI-facing changes.
- Smoke-test `list-bots`, `search`, and one `download` path when you touch runtime behavior.
- When validating packaging, build a wheel and run commands from a directory outside the repository.
