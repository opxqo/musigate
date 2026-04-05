from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class Step(BaseModel):
    action: str
    content: Optional[str] = None
    expect: Optional[str] = None
    timeout: Optional[int] = None
    strategy: Optional[str] = None
    query: Optional[str] = None
    output: Optional[str] = None
    cases: Optional[List[Dict[str, Any]]] = None
    extract: Optional[Dict[str, str]] = None
    message: Optional[str] = None


class CommandDef(BaseModel):
    steps: List[Step]


class BotSettings(BaseModel):
    timeout: int = 15
    retry: int = 2


class BotConfig(BaseModel):
    name: str
    bot_username: str
    description: str = ""
    version: str = "1.0"
    settings: BotSettings = Field(default_factory=BotSettings)
    commands: Dict[str, CommandDef]


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_PACKAGE = "musigate.resources"


def _bot_filename(bot_name: str) -> str:
    return bot_name if bot_name.endswith(".yaml") else f"{bot_name}.yaml"


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    unique_paths: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path.expanduser().resolve(strict=False)).lower()
        if key in seen:
            continue
        seen.add(key)
        unique_paths.append(path)
    return unique_paths


def _external_bot_dirs() -> list[Path]:
    return _dedupe_paths(
        [
            Path.cwd() / "bots",
            PROJECT_ROOT / "bots",
        ]
    )


def _explicit_bot_candidates(bot_name: str) -> list[Path]:
    candidate = Path(bot_name).expanduser()
    candidates: list[Path] = []

    if candidate.is_absolute() or candidate.parent != Path("."):
        candidates.append(candidate if candidate.is_absolute() else (Path.cwd() / candidate))
    elif candidate.suffix == ".yaml":
        candidates.extend(
            [
                Path.cwd() / candidate,
                PROJECT_ROOT / candidate,
            ]
        )

    return _dedupe_paths(candidates)


def _packaged_bot_resource(filename: str) -> Traversable | None:
    resource = resources.files(RESOURCE_PACKAGE).joinpath("bots", filename)
    return resource if resource.is_file() else None


def _read_yaml(source: Path | Traversable) -> dict:
    if isinstance(source, Path):
        raw = source.read_text(encoding="utf-8")
    else:
        raw = source.read_text(encoding="utf-8")
    return yaml.safe_load(raw) or {}


def _resolve_bot_source(bot_name: str) -> Path | Traversable:
    for candidate in _explicit_bot_candidates(bot_name):
        if candidate.is_file():
            return candidate

    filename = _bot_filename(bot_name)
    for directory in _external_bot_dirs():
        candidate = directory / filename
        if candidate.is_file():
            return candidate

    packaged = _packaged_bot_resource(filename)
    if packaged is not None:
        return packaged

    searched = [str(path) for path in _explicit_bot_candidates(bot_name)]
    searched.extend(str(directory / filename) for directory in _external_bot_dirs())
    raise FileNotFoundError(f"Bot config not found: {filename}. Searched: {', '.join(searched)}")


def load_bot(bot_name: str) -> dict:
    """Load and validate a bot configuration."""
    data = _read_yaml(_resolve_bot_source(bot_name))
    config = BotConfig(**data)
    return config.model_dump()


def list_bots() -> list[dict]:
    configs: list[dict] = []
    seen_names: set[str] = set()

    for directory in _external_bot_dirs():
        if not directory.exists():
            continue
        for bot_file in sorted(directory.glob("*.yaml")):
            if bot_file.name == "template.yaml" or bot_file.name in seen_names:
                continue
            configs.append(load_bot(str(bot_file)))
            seen_names.add(bot_file.name)

    packaged_dir = resources.files(RESOURCE_PACKAGE).joinpath("bots")
    for bot_file in sorted(packaged_dir.iterdir(), key=lambda item: item.name):
        if not bot_file.is_file() or not bot_file.name.endswith(".yaml"):
            continue
        if bot_file.name == "template.yaml" or bot_file.name in seen_names:
            continue
        configs.append(load_bot(bot_file.name))
        seen_names.add(bot_file.name)

    return configs
