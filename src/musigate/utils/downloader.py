from pathlib import Path
from time import monotonic

from rich.console import Console

from musigate.utils.helper import ensure_directory, sanitize_filename


class Downloader:
    def __init__(self, client):
        self.client = client
        self.console = Console()

    async def save(
        self,
        media,
        output_dir: str,
        filename: str,
        show_progress: bool = False,
    ):
        output_path = ensure_directory(output_dir)
        safe_filename = sanitize_filename(Path(filename).name)
        file_path = output_path / safe_filename

        progress_callback = None
        progress_state = None
        if show_progress:
            self.console.print(f"INFO: Downloading {safe_filename} -> {file_path}", style="cyan")
            progress_state = self._build_progress_state()
            progress_callback = self._build_progress_callback(progress_state)

        await self.client.download_media(
            media,
            file=str(file_path),
            progress_callback=progress_callback,
        )

        if show_progress:
            file_size = file_path.stat().st_size if file_path.exists() else None
            size_hint = f" ({self._format_bytes(file_size)})" if file_size is not None else ""
            elapsed = None
            average_speed = None
            if progress_state is not None:
                elapsed = max(monotonic() - progress_state["started_at"], 0.0)
                if file_size and elapsed > 0:
                    average_speed = file_size / elapsed

            duration_hint = (
                f" in {self._format_duration(elapsed)}" if elapsed is not None else ""
            )
            speed_hint = (
                f" at avg {self._format_bytes_per_second(average_speed)}"
                if average_speed is not None
                else ""
            )
            self.console.print(
                f"INFO: Download finished -> {file_path}{size_hint}{duration_hint}{speed_hint}",
                style="green",
            )

        return str(file_path)

    def _build_progress_state(self):
        return {
            "last_percent": -1,
            "last_emit_at": monotonic(),
            "started_at": monotonic(),
        }

    def _build_progress_callback(self, state: dict[str, float | int]):
        def progress_callback(current: int, total: int):
            if total <= 0:
                return

            percent = int((current / total) * 100)
            now = monotonic()
            should_emit = percent >= 100 or percent // 10 > state["last_percent"] // 10
            should_emit = should_emit or (now - state["last_emit_at"] >= 15 and percent > state["last_percent"])

            if not should_emit:
                return

            elapsed = max(now - state["started_at"], 0.0)
            speed = current / elapsed if elapsed > 0 else None
            eta_seconds = ((total - current) / speed) if speed and speed > 0 and current < total else 0
            state["last_percent"] = percent
            state["last_emit_at"] = now
            self.console.print(
                f"INFO: Download progress {percent:>3}% "
                f"({self._format_bytes(current)} / {self._format_bytes(total)}) "
                f"at {self._format_bytes_per_second(speed)} "
                f"ETA {self._format_duration(eta_seconds)}",
                style="cyan",
            )

        return progress_callback

    def _format_bytes(self, value: int | None) -> str:
        if value is None:
            return "unknown"

        size = float(value)
        units = ["B", "KB", "MB", "GB", "TB"]
        for unit in units:
            if size < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{value} B"

    def _format_bytes_per_second(self, value: float | None) -> str:
        if value is None or value <= 0:
            return "unknown/s"
        return f"{self._format_bytes(int(value))}/s"

    def _format_duration(self, seconds: float | int | None) -> str:
        if seconds is None:
            return "unknown"

        total_seconds = max(int(seconds), 0)
        minutes, secs = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
