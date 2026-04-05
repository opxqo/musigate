import asyncio
import re
from pathlib import Path

from telethon import events


TRACK_LINE_PREFIX = "\u6b4c\u66f2"
ALBUM_LINE_PREFIX = "\u4e13\u8f91"
TITLE_QUOTES = "\u300c\u300d\u300e\u300f\u201c\u201d"


class Listener:
    def __init__(self, client, bot_username: str):
        self.client = client
        self.bot = bot_username

    async def wait(self, expect: str, timeout: int = 15, after_message_id: int | None = None):
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        @self.client.on(events.NewMessage(from_users=self.bot))
        async def handler(event):
            response = self._parse(event.message, expect)
            if response:
                if not future.done():
                    future.set_result(response)
                self.client.remove_event_handler(handler)

        try:
            recent = await self._find_recent_match(expect, after_message_id=after_message_id)
            if recent is not None:
                if not future.done():
                    future.set_result(recent)
                self.client.remove_event_handler(handler)
                return recent
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.client.remove_event_handler(handler)
            raise TimeoutError(f"Timed out waiting for {expect} ({timeout}s)")

    def _parse(self, message, expect: str):
        parsed = self._parse_any(message)
        if expect == "any":
            return parsed
        if parsed and parsed["type"] == expect:
            return parsed
        return None

    def _parse_any(self, message):
        if message.audio:
            return self._parse_audio(message)
        if message.buttons:
            return {
                "type": "inline_buttons",
                "text": message.text or "",
                "buttons": [
                    [
                        {"text": btn.text, "data": btn.data, "_message": message}
                        for btn in row
                    ]
                    for row in message.buttons
                ],
            }
        if message.document:
            return {
                "type": "document",
                "text": message.text or "",
                "file": message.media,
                "ext": self._message_extension(message),
            }
        if message.text:
            return {
                "type": "text_message",
                "text": message.text,
            }
        return None

    def _parse_audio(self, message):
        audio = message.audio
        document = getattr(message, "document", None)
        audio_attr = self._document_attribute(document, "DocumentAttributeAudio")
        file_attr = self._document_attribute(document, "DocumentAttributeFilename")
        file_name = (
            getattr(message.file, "name", None)
            or getattr(file_attr, "file_name", None)
        )
        parsed_from_text = self._parse_track_from_text(message.text or "")
        parsed_from_file = self._parse_track_from_filename(file_name)
        duration = getattr(audio, "duration", None)
        if duration is None:
            duration = getattr(audio_attr, "duration", None)
        mime_type = getattr(document, "mime_type", None)
        size = getattr(document, "size", None)

        performer = (
            getattr(audio, "performer", None)
            or getattr(audio_attr, "performer", None)
            or parsed_from_text["artist"]
            or parsed_from_file["artist"]
            or "unknown"
        )
        title = (
            getattr(audio, "title", None)
            or getattr(audio_attr, "title", None)
            or parsed_from_text["title"]
            or parsed_from_file["title"]
            or file_name
            or "unknown"
        )

        return {
            "type": "audio_file",
            "text": message.text or "",
            "artist": performer,
            "title": title,
            "ext": self._message_extension(message, fallback="mp3"),
            "duration": duration,
            "mime_type": mime_type,
            "size": size,
            "file": message.media,
            "file_name": file_name,
        }

    def _document_attribute(self, document, attribute_name: str):
        attributes = getattr(document, "attributes", None) or []
        for attribute in attributes:
            if attribute.__class__.__name__ == attribute_name:
                return attribute
        return None

    def _parse_track_from_text(self, text: str) -> dict[str, str | None]:
        if not text:
            return {"title": None, "artist": None}

        explicit_pattern = re.compile(
            rf"^{TRACK_LINE_PREFIX}[:\uff1a]\s*(?P<title>.+?)\s*-\s*(?P<artist>.+?)\s*$"
        )
        generic_pattern = re.compile(
            rf"^[{TITLE_QUOTES}\"]?(?P<title>.+?)[{TITLE_QUOTES}\"]?\s*-\s*(?P<artist>.+?)\s*$"
        )

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            explicit_match = explicit_pattern.match(stripped)
            if explicit_match:
                return {
                    "title": explicit_match.group("title").strip(),
                    "artist": explicit_match.group("artist").strip(),
                }

            generic_match = generic_pattern.match(stripped)
            if generic_match and not stripped.startswith((ALBUM_LINE_PREFIX, "#", "via ")):
                return {
                    "title": generic_match.group("title").strip(),
                    "artist": generic_match.group("artist").strip(),
                }

        return {"title": None, "artist": None}

    def _parse_track_from_filename(self, file_name: str | None) -> dict[str, str | None]:
        if not file_name:
            return {"title": None, "artist": None}

        stem = Path(file_name).stem.strip()
        if not stem:
            return {"title": None, "artist": None}

        match = re.match(r"^(?P<title>.+?)\s*-\s*(?P<artist>.+?)\s*$", stem)
        if not match:
            return {"title": stem, "artist": None}

        return {
            "title": match.group("title").strip(),
            "artist": match.group("artist").strip(),
        }

    def _message_extension(self, message, fallback: str = "bin") -> str:
        ext = getattr(message.file, "ext", None)
        if ext:
            return ext.lstrip(".")
        name = getattr(message.file, "name", None)
        if name and "." in name:
            return name.rsplit(".", 1)[-1]
        return fallback

    async def _find_recent_match(self, expect: str, after_message_id: int | None = None):
        messages = await self.client.get_messages(self.bot, limit=10)
        candidates = []
        for message in reversed(messages):
            if getattr(message, "out", False):
                continue
            if after_message_id is not None and message.id <= after_message_id:
                continue
            parsed = self._parse(message, expect)
            if parsed is not None:
                candidates.append(parsed)

        if candidates:
            return candidates[0]
        return None
