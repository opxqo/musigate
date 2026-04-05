# Adapter Workflow

## Existing patterns

Reference adapters:

- [bots/music163.yaml](../../../bots/music163.yaml)
- [bots/music_v1.yaml](../../../bots/music_v1.yaml)

These adapters currently model the common case:

1. Send `/search {query}`
2. Wait for `inline_buttons`
3. Pick a numbered result with `match_text_index`
4. Wait for `audio_file`
5. Download the file

## Core code map

- Adapter loading: [src/musigate/adapters/loader.py](../../../src/musigate/adapters/loader.py)
- Engine context: [src/musigate/gateway/engine.py](../../../src/musigate/gateway/engine.py)
- Step execution: [src/musigate/gateway/executor.py](../../../src/musigate/gateway/executor.py)
- Button strategy logic: [src/musigate/gateway/selector.py](../../../src/musigate/gateway/selector.py)
- Telegram message parsing: [src/musigate/telegram/listener.py](../../../src/musigate/telegram/listener.py)
- Generic probe utility: [tmp_probe_bot.py](../../../tmp_probe_bot.py)

## When to change Python

Change YAML only when the bot can already be expressed with:

- `send_message`
- `wait_response`
- `click_button`
- `download`
- `respond_list`
- `respond_buttons`
- `branch`

Change Python when the bot needs:

- A new response shape not covered by `text_message`, `inline_buttons`, `audio_file`, or `document`
- A new selection algorithm beyond `first`, `last`, `match_title`, `match_text_index`, or `match_index N`
- A new executor action

## Release reminder

If the new adapter should work from an installed wheel, keep these two copies aligned:

- Development copy: [bots](../../../bots)
- Packaged copy: [src/musigate/resources/bots](../../../src/musigate/resources/bots)
