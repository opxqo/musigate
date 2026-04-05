# Musigate CLI Commands

## Development entrypoint

Use the repo virtualenv entrypoint during development:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli <command> ...
```

## Common commands

List adapters:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli list-bots
.\.venv\Scripts\python.exe -m musigate.cli list-bots --json
```

Login:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli login
```

Search:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli search "海底" --bot music_v1
.\.venv\Scripts\python.exe -m musigate.cli search "海底" --bot music_v1 --json
```

Download with smart matching:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli download "海底" --bot music_v1
```

Download a specific numbered result:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli download "海底" --bot music_v1 --pick 2
```

Download to a custom directory:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli download "海底" --bot music_v1 --pick 2 --output .\downloads\favorites
```

Inspect machine-readable download output:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli download "海底" --bot music_v1 --pick 2 --json
```

## Relevant files

- CLI entrypoint: [src/musigate/cli.py](../../../src/musigate/cli.py)
- Adapter loader: [src/musigate/adapters/loader.py](../../../src/musigate/adapters/loader.py)
- Download progress: [src/musigate/utils/downloader.py](../../../src/musigate/utils/downloader.py)
- Metadata parsing: [src/musigate/telegram/listener.py](../../../src/musigate/telegram/listener.py)
