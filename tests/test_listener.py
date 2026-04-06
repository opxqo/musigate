from types import SimpleNamespace

import pytest

from musigate.telegram.listener import Listener


class FakeClient:
    def __init__(self, messages):
        self._messages = messages
        self.handlers = []
        self.raise_on_get_messages = None

    def on(self, _event):
        def decorator(handler):
            self.handlers.append(handler)
            return handler

        return decorator

    def remove_event_handler(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)

    async def get_messages(self, _bot, limit=10):
        if self.raise_on_get_messages is not None:
            raise self.raise_on_get_messages
        return self._messages[:limit]


def make_message(message_id, *, out=False, text="", buttons=None, audio=None, document=None, media=None, file=None):
    return SimpleNamespace(
        id=message_id,
        out=out,
        text=text,
        buttons=buttons,
        audio=audio,
        document=document,
        media=media,
        file=file or SimpleNamespace(ext=".mp3", name="song.mp3"),
    )


def make_button(text, data=b"1"):
    return SimpleNamespace(text=text, data=data)


@pytest.mark.asyncio
async def test_listener_wait_reads_recent_matching_message():
    recent_response = make_message(
        11,
        out=False,
        text="1. Numb - Linkin Park",
        buttons=[[make_button("1")]],
    )
    client = FakeClient([recent_response])
    listener = Listener(client, "@testbot")

    result = await listener.wait("inline_buttons", timeout=1, after_message_id=10)

    assert result["type"] == "inline_buttons"
    assert result["buttons"][0][0]["text"] == "1"
    assert client.handlers == []


@pytest.mark.asyncio
async def test_listener_wait_cleans_handler_on_timeout():
    client = FakeClient([])
    listener = Listener(client, "@testbot")

    with pytest.raises(TimeoutError):
        await listener.wait("inline_buttons", timeout=0.01)

    assert client.handlers == []


@pytest.mark.asyncio
async def test_listener_wait_cleans_handler_when_recent_lookup_fails():
    client = FakeClient([])
    client.raise_on_get_messages = RuntimeError("boom")
    listener = Listener(client, "@testbot")

    with pytest.raises(RuntimeError, match="boom"):
        await listener.wait("inline_buttons", timeout=0.01)

    assert client.handlers == []


def test_listener_parse_audio_uses_message_text_when_metadata_missing():
    listener = Listener(FakeClient([]), "@testbot")
    message = make_message(
        1,
        text="\u6b4c\u66f2\uff1a\u4e0d\u51e1 - \u738b\u94ee\u4eae\n\u4e13\u8f91\uff1a\u51e1\u4eba\u4fee\u4ed9\u4f20",
        audio=SimpleNamespace(title=None, performer=None, duration=None),
        document=SimpleNamespace(mime_type="audio/x-flac", size=48905807),
        media="mock_media",
        file=SimpleNamespace(ext=".flac", name="\u4e0d\u51e1-\u738b\u94ee\u4eae.flac"),
    )

    result = listener._parse_audio(message)

    assert result["title"] == "\u4e0d\u51e1"
    assert result["artist"] == "\u738b\u94ee\u4eae"
    assert result["ext"] == "flac"
    assert result["mime_type"] == "audio/x-flac"
    assert result["size"] == 48905807
    assert result["duration"] is None


def test_listener_parse_audio_falls_back_to_filename():
    listener = Listener(FakeClient([]), "@testbot")
    audio_attribute = type(
        "DocumentAttributeAudio",
        (),
        {"title": None, "performer": None, "duration": 211},
    )()
    filename_attribute = type(
        "DocumentAttributeFilename",
        (),
        {"file_name": "\u4e0d\u51e1-\u738b\u94ee\u4eae.flac"},
    )()
    message = make_message(
        2,
        text="",
        audio=SimpleNamespace(title=None, performer=None, duration=211),
        document=SimpleNamespace(
            mime_type="audio/x-flac",
            size=48905807,
            attributes=[audio_attribute, filename_attribute],
        ),
        media="mock_media",
        file=SimpleNamespace(ext=".flac", name="\u4e0d\u51e1-\u738b\u94ee\u4eae.flac"),
    )

    result = listener._parse_audio(message)

    assert result["title"] == "\u4e0d\u51e1"
    assert result["artist"] == "\u738b\u94ee\u4eae"
    assert result["file_name"] == "\u4e0d\u51e1-\u738b\u94ee\u4eae.flac"
    assert result["duration"] == 211
    assert result["mime_type"] == "audio/x-flac"
    assert result["size"] == 48905807


def test_listener_parse_audio_reads_duration_from_document_attributes():
    listener = Listener(FakeClient([]), "@testbot")
    audio_attribute = type(
        "DocumentAttributeAudio",
        (),
        {"title": "\u4e0d\u51e1", "performer": "\u738b\u94ee\u4eae", "duration": 211},
    )()
    message = make_message(
        3,
        text="",
        audio=SimpleNamespace(title=None, performer=None, duration=None),
        document=SimpleNamespace(
            mime_type="audio/x-flac",
            size=48905807,
            attributes=[audio_attribute],
        ),
        media="mock_media",
        file=SimpleNamespace(ext=".flac", name="\u4e0d\u51e1-\u738b\u94ee\u4eae.flac"),
    )

    result = listener._parse_audio(message)

    assert result["title"] == "\u4e0d\u51e1"
    assert result["artist"] == "\u738b\u94ee\u4eae"
    assert result["duration"] == 211
