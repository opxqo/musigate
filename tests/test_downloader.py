from pathlib import Path

import pytest

from musigate.utils.downloader import Downloader


class FakeDownloadClient:
    def __init__(self):
        self.calls = []

    async def download_media(self, media, file: str, progress_callback=None):
        self.calls.append(
            {
                "media": media,
                "file": file,
                "progress_callback": progress_callback,
            }
        )
        if progress_callback is not None:
            progress_callback(1024, 4096)
            progress_callback(4096, 4096)

        Path(file).write_bytes(b"x" * 4096)
        return file


@pytest.mark.asyncio
async def test_downloader_save_emits_progress_messages(tmp_path):
    client = FakeDownloadClient()
    downloader = Downloader(client)
    messages = []

    def fake_print(message, *args, **kwargs):
        messages.append(str(message))

    downloader.console.print = fake_print

    saved_path = await downloader.save(
        media="mock_media",
        output_dir=str(tmp_path),
        filename="song.mp3",
        show_progress=True,
    )

    assert saved_path.endswith("song.mp3")
    assert client.calls[0]["progress_callback"] is not None
    assert any("Downloading song.mp3" in message for message in messages)
    assert any("Download progress" in message for message in messages)
    assert any("ETA" in message and "/s" in message for message in messages)
    assert any("Download finished" in message for message in messages)
