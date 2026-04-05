import pytest

from musigate.telegram.client import Client


class FakeTelethonClient:
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
        return file


@pytest.mark.asyncio
async def test_client_download_media_forwards_progress_callback():
    wrapped = Client.__new__(Client)
    wrapped.client = FakeTelethonClient()
    progress_callback = object()

    result = await wrapped.download_media(
        "mock_media",
        file="downloads/song.mp3",
        progress_callback=progress_callback,
    )

    assert result == "downloads/song.mp3"
    assert wrapped.client.calls == [
        {
            "media": "mock_media",
            "file": "downloads/song.mp3",
            "progress_callback": progress_callback,
        }
    ]
