import re
from pathlib import Path
from typing import Any


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _resolve_context_value(context: dict[str, Any], key: str, default: str = "") -> Any:
    current: Any = context
    for part in key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def render_template(template: str, context: dict[str, Any]) -> str:
    """Render a string template with simple `{key}` or `{nested.key}` placeholders."""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return str(_resolve_context_value(context, key, ""))

    return re.sub(r"\{([^}]+)\}", replace, template)


def sanitize_filename(filename: str) -> str:
    """Remove characters that are invalid on Windows and trim empty segments."""
    sanitized = INVALID_FILENAME_CHARS.sub("_", filename).strip().rstrip(".")
    return sanitized or "downloaded_file"


def ensure_directory(path: str) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
