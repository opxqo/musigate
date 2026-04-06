# Adapter Workflow

## Reference adapters

- Development copies:
  - [bots/music163.yaml](../../../bots/music163.yaml)
  - [bots/music_v1.yaml](../../../bots/music_v1.yaml)
- Packaged copies:
  - [src/musigate/resources/bots/music163.yaml](../../../src/musigate/resources/bots/music163.yaml)
  - [src/musigate/resources/bots/music_v1.yaml](../../../src/musigate/resources/bots/music_v1.yaml)

The most common current pattern is:

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
- Telegram parsing: [src/musigate/telegram/listener.py](../../../src/musigate/telegram/listener.py)
- Probe utility: [tmp_probe_bot.py](../../../tmp_probe_bot.py)

## When YAML is enough

Stay in YAML when the bot can be expressed with:

- `send_message`
- `wait_response`
- `click_button`
- `download`
- `respond_list`
- `respond_buttons`
- `branch`

## When Python must change

Change Python only if the bot needs one of these:

- A response shape not covered by `text_message`, `inline_buttons`, `audio_file`, or `document`
- A selection rule beyond the current selector strategies
- A new executor action
- A real CLI surface change

## Release reminder

If the adapter should work from an installed package, keep both copies aligned:

- Development copy: [bots](../../../bots)
- Packaged copy: [src/musigate/resources/bots](../../../src/musigate/resources/bots)
