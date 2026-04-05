import os
from copy import deepcopy
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_PACKAGE = "musigate.resources"
DEFAULT_SETTINGS = {
    "telegram": {
        "apiId": "",
        "apiHash": "",
        "phone": "",
        "sessionName": "musigate",
        "proxy": {
            "enabled": False,
            "type": "socks5",
            "host": "127.0.0.1",
            "port": 7897,
            "username": "",
            "password": "",
        },
    },
    "download": {
        "defaultOutput": "./downloads",
        "filenameTemplate": "{artist}-{title}.{ext}",
    },
    "logging": {
        "level": "INFO",
        "file": "logs/musigate.log",
    },
}


def _merge_dict(base: dict, updates: dict) -> dict:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dict(base[key], value)
        else:
            base[key] = value
    return base


def _read_yaml(source: Path | Traversable) -> dict:
    if isinstance(source, Path):
        raw = source.read_text(encoding="utf-8")
    else:
        raw = source.read_text(encoding="utf-8")
    return yaml.safe_load(raw) or {}


def _config_candidates() -> list[Path]:
    candidates: list[Path] = []
    custom_path = os.getenv("MUSIGATE_SETTINGS_FILE")
    if custom_path:
        candidates.append(Path(custom_path).expanduser())

    candidates.extend(
        [
            Path.cwd() / "config" / "settings.yaml",
            PROJECT_ROOT / "config" / "settings.yaml",
        ]
    )
    return candidates


def _packaged_settings_resource() -> Traversable:
    return resources.files(RESOURCE_PACKAGE).joinpath("config", "settings.yaml")


def _load_settings_overrides() -> dict:
    for candidate in _config_candidates():
        if candidate.is_file():
            return _read_yaml(candidate)
    return _read_yaml(_packaged_settings_resource())


def load_settings():
    """Load settings from .env, external config, and packaged defaults."""
    load_dotenv()
    settings = deepcopy(DEFAULT_SETTINGS)
    _merge_dict(settings, _load_settings_overrides())

    api_id = os.getenv("TELEGRAM_API_ID")
    if api_id:
        settings["telegram"]["apiId"] = int(api_id) if api_id.isdigit() else api_id

    api_hash = os.getenv("TELEGRAM_API_HASH")
    if api_hash:
        settings["telegram"]["apiHash"] = api_hash

    phone = os.getenv("TELEGRAM_PHONE")
    if phone:
        settings["telegram"]["phone"] = phone

    session_name = os.getenv("TELEGRAM_SESSION_NAME")
    if session_name:
        settings["telegram"]["sessionName"] = session_name

    proxy_enabled = os.getenv("TELEGRAM_PROXY_ENABLED")
    if proxy_enabled is not None:
        settings["telegram"]["proxy"]["enabled"] = proxy_enabled.lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    proxy_type = os.getenv("TELEGRAM_PROXY_TYPE")
    if proxy_type:
        settings["telegram"]["proxy"]["type"] = proxy_type

    proxy_host = os.getenv("TELEGRAM_PROXY_HOST")
    if proxy_host:
        settings["telegram"]["proxy"]["host"] = proxy_host

    proxy_port = os.getenv("TELEGRAM_PROXY_PORT")
    if proxy_port:
        settings["telegram"]["proxy"]["port"] = int(proxy_port)

    proxy_username = os.getenv("TELEGRAM_PROXY_USERNAME")
    if proxy_username:
        settings["telegram"]["proxy"]["username"] = proxy_username

    proxy_password = os.getenv("TELEGRAM_PROXY_PASSWORD")
    if proxy_password:
        settings["telegram"]["proxy"]["password"] = proxy_password

    return settings


def validate_telegram_settings(settings: dict) -> None:
    telegram = settings.get("telegram", {})
    missing = []
    if not telegram.get("apiId"):
        missing.append("telegram.apiId / TELEGRAM_API_ID")
    if not telegram.get("apiHash"):
        missing.append("telegram.apiHash / TELEGRAM_API_HASH")
    if missing:
        raise ValueError("Missing Telegram settings: " + ", ".join(missing))


def build_telegram_proxy(settings: dict) -> tuple | None:
    proxy = settings.get("telegram", {}).get("proxy", {})
    if not proxy.get("enabled"):
        return None

    proxy_type = str(proxy.get("type", "socks5")).lower()
    host = proxy.get("host")
    port = proxy.get("port")
    username = proxy.get("username") or None
    password = proxy.get("password") or None
    if not host or not port:
        raise ValueError("Telegram proxy is enabled, but host or port is missing")

    if username or password:
        return (proxy_type, host, int(port), True, username, password)
    return (proxy_type, host, int(port))
