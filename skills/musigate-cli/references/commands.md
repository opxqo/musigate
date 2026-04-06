# Musigate CLI Commands

## Development entrypoint

In repo development, prefer the repo virtualenv entrypoint for reliability:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli <command> ...
```

## Baseline commands

List adapters:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli list-bots
.\.venv\Scripts\python.exe -m musigate.cli list-bots --json
```

Login with interactive credential capture:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli login
```

Login with explicit credentials:

```powershell
.\.venv\Scripts\python.exe -m musigate.cli login --api-id 123456 --api-hash your_hash
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
- Config and credential paths: [src/musigate/utils/config.py](../../../src/musigate/utils/config.py)
- Adapter loader: [src/musigate/adapters/loader.py](../../../src/musigate/adapters/loader.py)
- Download progress: [src/musigate/utils/downloader.py](../../../src/musigate/utils/downloader.py)
- Metadata parsing: [src/musigate/telegram/listener.py](../../../src/musigate/telegram/listener.py)
