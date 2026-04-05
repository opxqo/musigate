'''
Author: opxqo 2547364328luo@wic.edu.kg
Date: 2026-04-05 09:51:07
LastEditors: opxqo 2547364328luo@wic.edu.kg
LastEditTime: 2026-04-05 09:59:18
FilePath: \\musigate\\src\\musigate\\telegram\\auth.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import os
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    FloodWaitError,
)
from rich.console import Console
from rich.prompt import Prompt

console = Console()

class TelegramAuth:
    def __init__(self, api_id: int, api_hash: str, session_name: str = "musigate", proxy=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash, proxy=proxy)

    async def login(self) -> bool:
        """
        完整登录流程：
        1. 检查是否已有 session，有则直接复用
        2. 没有则引导用户输入手机号
        3. 发送验证码
        4. 用户输入验证码完成登录
        """
        await self.client.connect()

        # 已登录则直接返回
        if await self.client.is_user_authorized():
            me = await self.client.get_me()
            console.print(f"[green]✔ 已登录账号：{me.first_name}（+{me.phone}）[/green]")
            return True

        # 未登录，开始登录流程
        console.print("[bold]📱 请登录你的 Telegram 账号[/bold]")
        phone = Prompt.ask("请输入手机号（含国际区号，如 +86xxxxxxxxxx）")

        try:
            await self.client.send_code_request(phone)
            console.print("[yellow]✔ 验证码已发送，请查看 Telegram 消息[/yellow]")
        except FloodWaitError as e:
            console.print(f"[red]✖ 请求过于频繁，请等待 {e.seconds} 秒后重试[/red]")
            return False

        # 输入验证码，最多重试 3 次
        for attempt in range(3):
            code = Prompt.ask("请输入收到的验证码")
            try:
                await self.client.sign_in(phone, code)
                break
            except PhoneCodeInvalidError:
                remaining = 2 - attempt
                if remaining > 0:
                    console.print(f"[red]✖ 验证码错误，还有 {remaining} 次机会[/red]")
                else:
                    console.print("[red]✖ 验证码错误次数过多，登录失败[/red]")
                    return False
            except PhoneCodeExpiredError:
                console.print("[red]✖ 验证码已过期，请重新运行登录命令[/red]")
                return False
            except SessionPasswordNeededError:
                console.print("[yellow]⚠ 该账号开启了两步验证[/yellow]")
                password = Prompt.ask("请输入两步验证密码", password=True)
                try:
                    await self.client.sign_in(password=password)
                    break
                except Exception:
                    console.print("[red]✖ 两步验证密码错误[/red]")
                    return False

        # 验证登录结果
        if await self.client.is_user_authorized():
            me = await self.client.get_me()
            console.print(f"[green]✔ 登录成功！欢迎，{me.first_name}[/green]")
            console.print(f"[dim]Session 已保存至 {self.session_name}.session，下次无需重新登录[/dim]")
            return True
        else:
            console.print("[red]✖ 登录失败[/red]")
            return False

    async def logout(self):
        """退出登录并删除 session 文件"""
        await self.client.log_out()
        session_file = f"{self.session_name}.session"
        if os.path.exists(session_file):
            os.remove(session_file)
        console.print("[green]✔ 已退出登录[/green]")

    async def disconnect(self):
        await self.client.disconnect()
