# musigate

`musigate` is a Python CLI for searching and downloading music through Telegram bots with a YAML-driven adapter system.

This release is an alpha build. The core CLI flow is working, but bot behavior still depends on upstream Telegram bots and may change over time.

## Install

From a published package:

```bash
pip install musigate
```

From a local wheel:

```bash
pip install dist/musigate-0.1.0a1-py3-none-any.whl
```

For development:

```bash
pip install -e .[dev]
```

## Setup

Copy `.env.example` to `.env`, then fill in your Telegram API credentials:

```bash
cp .env.example .env
```

Required values:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`

## Built-in Bots

- `music163`
- `music_v1`

## Usage

Login to Telegram:

```bash
musigate login
```

Search only:

```bash
musigate search "Numb" --bot music163
```

Download with smart matching:

```bash
musigate download "Numb" --bot music163
```

Download a specific numbered search result:

```bash
musigate download "海底" --bot music_v1 --pick 2
```

Write files to a custom directory:

```bash
musigate download "海底" --bot music_v1 --pick 2 --output ./downloads/favorites
```

Machine-readable JSON output:

```bash
musigate search "Numb" --bot music163 --json
musigate download "Numb" --bot music163 --json
musigate list-bots --json
```

Normal CLI downloads show periodic progress updates including speed and ETA.
