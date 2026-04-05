"""Telegram client wrapper used by musigate."""
from telethon import TelegramClient

class Client:
    def __init__(self, api_id, api_hash, session_name="musigate", proxy=None):
        self.client = TelegramClient(session_name, api_id, api_hash, proxy=proxy)

    async def connect(self, require_authorized: bool = True):
        await self.client.connect()
        if require_authorized and not await self.client.is_user_authorized():
            raise RuntimeError("请先执行 `musigate login` 完成 Telegram 登录")

    async def send_message(self, bot: str, text: str):
        return await self.client.send_message(bot, text)

    async def click_button(self, button: dict):
        # 通过 Telethon 点击内联按钮
        msg = button["_message"]
        await msg.click(data=button["data"])

    async def disconnect(self):
        await self.client.disconnect()

    async def download_media(self, media, file: str, progress_callback=None):
        return await self.client.download_media(
            media,
            file=file,
            progress_callback=progress_callback,
        )

    async def is_authorized(self) -> bool:
        return await self.client.is_user_authorized()
