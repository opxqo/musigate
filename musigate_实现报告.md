# musigate 项目实现报告

**项目名称：** musigate  
**开发语言：** Python  
**文档版本：** v2.0  
**日期：** 2026-04-05

---

## 一、项目概述

musigate 是一个基于 Python 的命令行工具（CLI），通过 Telegram App API（MTProto 协议）对接各类音乐下载机器人，实现统一入口的音乐下载能力。整个系统采用配置驱动架构，用户只需编写 YAML 文件即可适配任意 Telegram 音乐机器人，无需修改核心代码。

该工具支持 AI Agent（如 OpenClaw 等）直接调用 CLI 命令完成音乐下载任务，具备良好的可扩展性和跨平台兼容性。

---

## 二、核心设计理念

### 2.1 配置驱动（Data-Driven）

每个 Telegram 机器人对应一个 YAML 适配文件，描述其交互方式和命令流程。核心引擎读取 YAML 文件并按步骤执行，新增机器人只需新增 YAML，无需改动任何代码。

### 2.2 两级命令体系

- **一级命令**：用户或 AI Agent 发给 CLI 的标准命令（如 `download`、`search`）
- **二级命令**：CLI 按照 YAML 配置发给 Telegram 机器人的具体操作（如 `send_message`、`click_button`）

### 2.3 Context 贯穿执行

每次执行维护一个 `context` 对象，存储查询词、上一步响应、提取数据、下载结果等状态，所有二级命令共享该上下文。

### 2.4 规则引擎替代 LLM

交互流程通过 YAML 规则精确描述，无需依赖大语言模型，执行更稳定、速度更快、不依赖外部 AI 接口。

---

## 三、项目结构

```
musigate/
├── pyproject.toml              # 项目依赖与元信息
├── README.md
├── .env.example                # 环境变量模板
├── .gitignore
│
├── config/
│   └── settings.yaml           # 全局配置（API凭证、下载路径等）
│
├── bots/                       # 机器人适配器目录
│   ├── template.yaml           # 新增机器人的配置模板
│   ├── vkmusic.yaml            # VKMusic 机器人适配
│   └── spotifybot.yaml         # SpotifyBot 机器人适配
│
├── src/
│   └── musigate/
│       ├── __init__.py
│       ├── cli.py              # CLI 入口（基于 Typer）
│       │
│       ├── gateway/
│       │   ├── __init__.py
│       │   ├── engine.py       # 核心规则引擎，编排二级命令执行
│       │   ├── executor.py     # 执行每个 action
│       │   └── selector.py     # 按钮选择策略
│       │
│       ├── telegram/
│       │   ├── __init__.py
│       │   ├── auth.py         # 登录模块（手机号+验证码+session复用）
│       │   ├── client.py       # Telethon 封装，管理 session 和连接
│       │   └── listener.py     # 监听消息回复，处理超时
│       │
│       ├── adapters/
│       │   ├── __init__.py
│       │   └── loader.py       # 加载并校验 YAML 适配文件
│       │
│       └── utils/
│           ├── __init__.py
│           ├── downloader.py   # 文件下载与本地保存
│           └── helper.py       # 通用工具函数（模板渲染、相似度计算等）
│
├── downloads/                  # 默认下载输出目录
│
└── tests/
    ├── test_engine.py
    ├── test_loader.py
    └── test_selector.py
```

---

## 四、技术栈

| 组件 | 库 | 用途 |
|---|---|---|
| Telegram 客户端 | Telethon | MTProto 协议，收发消息、点击按钮、下载文件 |
| CLI 框架 | Typer | 命令行参数解析与命令注册 |
| YAML 解析 | PyYAML | 读取机器人适配配置文件 |
| 终端美化 | Rich | 进度条、彩色日志、状态提示 |
| 异步文件 | aiofiles | 异步写入下载文件 |
| 配置管理 | python-dotenv | 管理 API 凭证等环境变量 |
| 数据校验 | Pydantic | YAML 结构校验 |
| 单元测试 | pytest | 测试引擎与选择器逻辑 |

---

## 五、YAML 配置规范

### 5.1 配置模板（bots/template.yaml）

```yaml
name: ""                        # 机器人显示名称
bot_username: ""                # Telegram 用户名，如 @vkmusic_bot
description: ""                 # 功能描述
version: "1.0"

settings:
  timeout: 15                   # 每步等待超时（秒）
  retry: 2                      # 失败重试次数

commands:

  search:                       # 一级命令：搜索
    steps:
      - action: send_message
        content: "{query}"
      - action: wait_response
        expect: inline_buttons
        timeout: 10
      - action: respond_buttons  # 将按钮列表返回给用户

  download:                     # 一级命令：搜索并下载
    steps:
      - action: send_message
        content: "{query}"
      - action: wait_response
        expect: inline_buttons
        timeout: 10
      - action: click_button
        strategy: match_title    # 选择最匹配歌名的按钮
      - action: wait_response
        expect: audio_file
        timeout: 30
      - action: download
        output: "{title}.{ext}"

  url:                          # 一级命令：链接直接下载
    steps:
      - action: send_message
        content: "{url}"
      - action: wait_response
        expect: audio_file
        timeout: 30
      - action: download
        output: "{title}.{ext}"
```

### 5.2 按钮选择策略（strategy）

| 策略 | 说明 |
|---|---|
| first | 选择第一个按钮 |
| last | 选择最后一个按钮 |
| match_title | 计算相似度，选择最接近查询词的按钮 |
| match_index N | 选择第 N 个按钮（从 0 开始） |

### 5.3 期望响应类型（expect）

| 类型 | 说明 |
|---|---|
| inline_buttons | 内联键盘按钮 |
| audio_file | 音频文件 |
| text_message | 纯文字消息 |
| document | 文件（非音频格式） |

---

## 六、核心模块实现

### 6.1 CLI 入口（cli.py）

```python
import typer
from musigate.gateway.engine import Engine
from musigate.adapters.loader import load_bot

app = typer.Typer()

@app.command()
def download(
    query: str = typer.Argument(..., help="歌名或关键词"),
    bot: str = typer.Option(..., "--bot", "-b", help="机器人名称"),
    output: str = typer.Option("./downloads", "--output", "-o", help="输出目录")
):
    """搜索并下载音乐"""
    bot_config = load_bot(bot)
    engine = Engine(bot_config)
    engine.run("download", query=query, output=output)

@app.command("list-bots")
def list_bots():
    """列出所有可用机器人"""
    ...

@app.command()
def test(
    bot: str = typer.Option(..., "--bot", "-b")
):
    """测试机器人是否可用"""
    ...

if __name__ == "__main__":
    app()
```

### 6.2 规则引擎（gateway/engine.py）

```python
import asyncio
from musigate.gateway.executor import Executor
from musigate.utils.helper import render_template

class Engine:
    def __init__(self, bot_config: dict):
        self.config = bot_config
        self.executor = Executor(bot_config)

    def run(self, command: str, **kwargs):
        asyncio.run(self._run_async(command, **kwargs))

    async def _run_async(self, command: str, **kwargs):
        # 找到一级命令对应的 steps
        command_def = self.config["commands"].get(command)
        if not command_def:
            raise ValueError(f"机器人不支持命令: {command}")

        # 初始化 context
        context = {
            "query": kwargs.get("query"),
            "url": kwargs.get("url"),
            "output": kwargs.get("output", "./downloads"),
            "lastResponse": None,
            "extractedData": {},
            "result": None
        }

        # 按步骤执行二级命令
        for step in command_def["steps"]:
            await self.executor.run(step, context)

        return context["result"]
```

### 6.3 执行器（gateway/executor.py）

```python
from musigate.gateway.selector import Selector
from musigate.utils.helper import render_template
from musigate.utils.downloader import Downloader

class Executor:
    def __init__(self, config):
        self.config = config
        self.selector = Selector()
        self.downloader = Downloader()

    async def run(self, step: dict, context: dict):
        action = step["action"]

        if action == "send_message":
            content = render_template(step["content"], context)
            await self.client.send_message(
                self.config["bot_username"], content
            )

        elif action == "wait_response":
            response = await self.listener.wait(
                expect=step["expect"],
                timeout=step.get("timeout", 15)
            )
            context["lastResponse"] = response

        elif action == "click_button":
            buttons = context["lastResponse"]["buttons"]
            button = self.selector.select(
                buttons,
                strategy=step["strategy"],
                query=context.get("query")
            )
            await self.client.click_button(button)

        elif action == "download":
            filename = render_template(
                step.get("output", "{title}.{ext}"), context
            )
            await self.downloader.save(
                context["lastResponse"]["file"],
                context["output"],
                filename
            )
            context["result"] = filename
```

### 6.4 按钮选择器（gateway/selector.py）

```python
from difflib import SequenceMatcher

class Selector:
    def select(self, buttons: list, strategy: str, query: str = None):
        flat = [btn for row in buttons for btn in row]

        if strategy == "first":
            return flat[0]

        elif strategy == "last":
            return flat[-1]

        elif strategy == "match_title":
            return max(flat, key=lambda b: self._similarity(b["text"], query))

        elif strategy.startswith("match_index"):
            index = int(strategy.split()[-1])
            return flat[index]

        raise ValueError(f"未知策略: {strategy}")

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
```

### 6.5 Telegram 客户端（telegram/client.py）

```python
from telethon import TelegramClient
from telethon.tl.types import KeyboardButtonCallback

class Client:
    def __init__(self, api_id, api_hash, session_name="musigate"):
        self.client = TelegramClient(session_name, api_id, api_hash)

    async def connect(self):
        await self.client.start()

    async def send_message(self, bot: str, text: str):
        await self.client.send_message(bot, text)

    async def click_button(self, button: dict):
        # 通过 Telethon 点击内联按钮
        msg = button["_message"]
        await msg.click(data=button["data"])

    async def disconnect(self):
        await self.client.disconnect()
```

### 6.6 消息监听器（telegram/listener.py）

```python
import asyncio
from telethon import events

class Listener:
    def __init__(self, client, bot_username: str):
        self.client = client
        self.bot = bot_username

    async def wait(self, expect: str, timeout: int = 15):
        future = asyncio.get_event_loop().create_future()

        @self.client.on(events.NewMessage(from_users=self.bot))
        async def handler(event):
            response = self._parse(event.message, expect)
            if response:
                future.set_result(response)
                self.client.remove_event_handler(handler)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"等待 {expect} 超时（{timeout}s）")

    def _parse(self, message, expect: str):
        if expect == "inline_buttons" and message.buttons:
            return {
                "type": "inline_buttons",
                "text": message.text,
                "buttons": [[
                    {"text": btn.text, "data": btn.data, "_message": message}
                    for btn in row
                ] for row in message.buttons]
            }
        elif expect == "audio_file" and message.audio:
            return {
                "type": "audio_file",
                "title": message.audio.title or "unknown",
                "ext": "mp3",
                "file": message.media
            }
        return None
```

---

## 七、登录模块实现

### 7.1 登录流程

Telegram MTProto 登录分两种情况：

```
首次登录：输入手机号 → 收到验证码 → 输入验证码 → （如有）两步验证密码 → 登录成功 → 保存 session
再次登录：读取本地 session 文件 → 自动恢复连接 → 无需重复操作
```

### 7.2 完整实现（telegram/auth.py）

```python
"""
musigate/telegram/auth.py
Telegram 手机号 + 验证码登录模块
"""

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
    def __init__(self, api_id: int, api_hash: str, session_name: str = "musigate"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash)

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
```

### 7.3 登录 CLI 命令（cli/commands/auth.py）

```python
import asyncio
import typer
from musigate.telegram.auth import TelegramAuth
from musigate.utils.config import load_settings

app = typer.Typer()

@app.command()
def login():
    """登录 Telegram 账号"""
    settings = load_settings()
    auth = TelegramAuth(
        api_id=settings["telegram"]["apiId"],
        api_hash=settings["telegram"]["apiHash"],
        session_name=settings["telegram"]["sessionName"],
    )
    success = asyncio.run(auth.login())
    if not success:
        raise typer.Exit(code=1)

@app.command()
def logout():
    """退出登录并清除 session"""
    settings = load_settings()
    auth = TelegramAuth(
        api_id=settings["telegram"]["apiId"],
        api_hash=settings["telegram"]["apiHash"],
        session_name=settings["telegram"]["sessionName"],
    )
    asyncio.run(auth.logout())
```

### 7.4 错误处理一览

| 错误 | 原因 | 处理方式 |
|---|---|---|
| FloodWaitError | 请求过于频繁 | 提示等待秒数后重试 |
| PhoneCodeInvalidError | 验证码错误 | 最多重试 3 次 |
| PhoneCodeExpiredError | 验证码过期 | 提示重新登录 |
| SessionPasswordNeededError | 开启了两步验证 | 引导输入两步验证密码 |

---

## 八、四种交互场景 YAML 规范

通过对主流音乐下载机器人的研究，归纳出四种标准交互模式，YAML 规范覆盖全部场景。

### 8.1 场景一：简单直发型

**交互流程：** 发消息 → 等文件 → 下载

**代表机器人：** `@MusicsHunterBot`、`@DeezLoad2Bot`

```yaml
name: MusicsHunter
bot_username: "@MusicsHunterBot"
description: "发送歌名直接返回音频文件"
version: "1.0"

settings:
  timeout: 30
  retry: 2

commands:
  download:
    steps:
      - action: send_message
        content: "{query}"

      - action: wait_response
        expect: audio_file
        timeout: 30

      - action: download
        output: "{title}.{ext}"

  url:
    steps:
      - action: send_message
        content: "{url}"

      - action: wait_response
        expect: audio_file
        timeout: 30

      - action: download
        output: "{title}.{ext}"
```

---

### 8.2 场景二：按钮选择型

**交互流程：** 发消息 → 等按钮 → 点按钮 → 等文件 → 下载

**代表机器人：** `@VKM_bot`、`@ytsongdl_bot`

```yaml
name: VKMusic
bot_username: "@VKM_bot"
description: "搜索后返回按钮列表，选择后返回文件"
version: "1.0"

settings:
  timeout: 15
  retry: 2

commands:
  download:
    steps:
      - action: send_message
        content: "{query}"

      - action: wait_response
        expect: inline_buttons
        timeout: 10

      - action: click_button
        strategy: match_title   # 选择最匹配歌名的按钮
        query: "{query}"

      - action: wait_response
        expect: audio_file
        timeout: 30

      - action: download
        output: "{title}.{ext}"

  search:
    steps:
      - action: send_message
        content: "{query}"

      - action: wait_response
        expect: inline_buttons
        timeout: 10

      - action: respond_buttons   # 将按钮列表返回给用户展示
```

**按钮选择策略（strategy）说明：**

| 策略 | 说明 | 适用场景 |
|---|---|---|
| first | 选第一个按钮 | 结果已按相关度排序 |
| last | 选最后一个按钮 | 特殊布局机器人 |
| match_title | 计算相似度选最匹配的 | 结果无序，需要精确匹配 |
| match_index N | 选第 N 个（从0开始） | 固定位置选择 |

---

### 8.3 场景三：多轮对话型

**交互流程：** 发命令 → 等文字列表 → 回复序号 → 等按钮 → 点按钮 → 等文件 → 下载

**代表机器人：** 部分命令式机器人

```yaml
name: MultiTurnBot
bot_username: "@multiturnbot"
description: "命令式搜索，文字列表返回，需回复序号选择"
version: "1.0"

settings:
  timeout: 15
  retry: 2

commands:
  download:
    steps:
      - action: send_message
        content: "/search {query}"       # 发送命令式搜索

      - action: wait_response
        expect: text_message
        timeout: 10
        extract:
          pattern: "^(\\d+)\\."          # 匹配 "1. 歌名" 格式
          save_as: result_list           # 存入 context

      - action: send_message
        content: "1"                     # 回复序号选第一个

      - action: wait_response
        expect: inline_buttons
        timeout: 10

      - action: click_button
        strategy: first

      - action: wait_response
        expect: audio_file
        timeout: 30

      - action: download
        output: "{title}.{ext}"
```

**extract 字段说明：**

```yaml
extract:
  pattern: "^(\\d+)\\."   # 正则表达式，提取列表序号
  save_as: result_list     # 提取结果存入 context，后续步骤可引用
```

---

### 8.4 场景四：条件分支型

**交互流程：** 发消息 → 等任意响应 → 根据响应类型走不同分支

**代表机器人：** 行为不固定、响应类型多样的机器人

```yaml
name: SmartBot
bot_username: "@smartbot"
description: "响应类型不固定，根据实际返回内容自动分支处理"
version: "1.0"

settings:
  timeout: 15
  retry: 2

commands:
  download:
    steps:
      - action: send_message
        content: "{query}"

      - action: wait_response
        expect: any                      # 不限定类型，收到什么都往下走
        timeout: 10

      - action: branch                   # 条件分支
        cases:

          - when:
              type: audio_file           # 直接返回了文件
            steps:
              - action: download
                output: "{title}.{ext}"

          - when:
              type: inline_buttons       # 返回了按钮列表
            steps:
              - action: click_button
                strategy: match_title
                query: "{query}"
              - action: wait_response
                expect: audio_file
                timeout: 30
              - action: download
                output: "{title}.{ext}"

          - when:
              type: text_message
              not_contains: "未找到"     # 文字列表（非错误）
            steps:
              - action: send_message
                content: "1"
              - action: wait_response
                expect: audio_file
                timeout: 30
              - action: download
                output: "{title}.{ext}"

          - when:
              type: text_message
              contains: "未找到"         # 错误消息
            steps:
              - action: error
                message: "未找到歌曲: {query}"
```

**branch 字段说明：**

| 字段 | 说明 |
|---|---|
| `expect: any` | 不限定响应类型，接受任何消息 |
| `when.type` | 匹配响应类型（audio_file / inline_buttons / text_message） |
| `when.contains` | 消息文字包含指定字符串 |
| `when.not_contains` | 消息文字不包含指定字符串 |
| `action: error` | 主动抛出错误，终止执行并输出提示 |

---

### 8.5 四种场景对比总结

| 场景 | 复杂度 | 关键 action | 代表机器人 |
|---|---|---|---|
| 简单直发型 | ⭐ | send_message → download | MusicsHunterBot |
| 按钮选择型 | ⭐⭐ | click_button + strategy | VKM_bot |
| 多轮对话型 | ⭐⭐⭐ | extract + 多次 send_message | 命令式机器人 |
| 条件分支型 | ⭐⭐⭐⭐ | branch + cases + when | 行为不固定的机器人 |

**engine.py 需要支持的核心能力：**

```
线性执行 steps         → 场景一、二、三
branch 条件判断        → 场景四
extract 正则提取       → 场景三
expect: any           → 场景四
contains/not_contains → 场景四
context 变量传递       → 全部场景
```

---

## 九、完整执行流程示例

以下模拟执行 `musigate download "Numb" --bot vkmusic` 的完整过程：

**步骤 1：CLI 解析一级命令**

```
command = "download"
query   = "Numb"
bot     = "vkmusic"
```

**步骤 2：loader 加载 bots/vkmusic.yaml，找到 download 命令的 steps**

**步骤 3：engine 初始化 context**

```python
context = { "query": "Numb", "lastResponse": None, "result": None }
```

**步骤 4：逐步执行二级命令**

```
二级命令① send_message
  → 发送 "Numb" 给 @vkmusic_bot

二级命令② wait_response（expect: inline_buttons）
  → 机器人返回按钮列表：
    [Numb - Linkin Park]
    [Numb - Linkin Park (Live)]
    [Numb/Encore - Jay-Z]
  → context.lastResponse = { type: "inline_buttons", buttons: [...] }

二级命令③ click_button（strategy: match_title）
  → 相似度计算：
    "Numb - Linkin Park"        → 0.91 ✅ 最高
    "Numb - Linkin Park (Live)" → 0.78
    "Numb/Encore - Jay-Z"       → 0.61
  → 点击 "Numb - Linkin Park"

二级命令④ wait_response（expect: audio_file）
  → 机器人发送音频文件
  → context.lastResponse = { type: "audio_file", title: "Numb", ext: "mp3" }

二级命令⑤ download
  → 保存至 ./downloads/Numb.mp3
```

**步骤 5：CLI 输出结果**

```
✔ 连接 @vkmusic_bot
✔ 搜索 "Numb"
✔ 匹配到 "Numb - Linkin Park"（相似度 0.91）
✔ 下载完成 4.2MB
✔ 已保存到 ./downloads/Numb.mp3
```

---

## 十、错误处理机制

| 错误类型 | 处理方式 |
|---|---|
| wait_response 超时 | 按 YAML retry 次数重试，仍失败则报错退出 |
| expect 类型不匹配 | 检查是否有 fallback 配置，否则报错 |
| 机器人无响应 | 超时后提示检查机器人状态 |
| 按钮未找到 | selector 抛出异常，engine 捕获后报错 |
| 文件下载失败 | 提示网络问题或磁盘空间不足 |
| YAML 格式错误 | Pydantic 校验失败时给出详细错误位置 |

---

## 十一、全局配置文件

```yaml
# config/settings.yaml
telegram:
  apiId: ""           # 从 my.telegram.org 获取
  apiHash: ""
  phone: ""
  sessionName: "musigate"

download:
  defaultOutput: "./downloads"
  filenameTemplate: "{artist}-{title}.{ext}"

logging:
  level: "INFO"
  file: "logs/musigate.log"
```

---

## 十二、CLI 命令一览

| 命令 | 说明 | 示例 |
|---|---|---|
| login | 登录 Telegram 账号 | `musigate login` |
| logout | 退出登录并清除 session | `musigate logout` |
| download | 搜索并下载音乐 | `musigate download "Numb" --bot vkmusic` |
| search | 仅搜索，返回结果列表 | `musigate search "Numb" --bot vkmusic` |
| url | 通过链接直接下载 | `musigate url "https://..." --bot vkmusic` |
| list-bots | 列出所有可用机器人 | `musigate list-bots` |
| test | 测试机器人是否可用 | `musigate test --bot vkmusic` |

---

## 十三、扩展新机器人

只需三步：

1. 复制 `bots/template.yaml`，重命名为新机器人名称
2. 填写 `bot_username`、`name`、`description`
3. 根据该机器人的实际交互方式，编写各命令的 `steps`

无需修改任何 Python 代码。

---

## 十四、开发路线图

| 阶段 | 任务 | 优先级 |
|---|---|---|
| 第一阶段 | adapters/loader.py，完成 YAML 加载与校验 | 高 |
| 第一阶段 | telegram/client.py，跑通 Telethon 连接 | 高 |
| 第二阶段 | gateway/engine.py + executor.py，实现核心引擎 | 高 |
| 第二阶段 | gateway/selector.py，实现按钮选择策略 | 高 |
| 第三阶段 | cli.py + bin 入口，接入命令行 | 中 |
| 第三阶段 | 编写 bots/vkmusic.yaml，端到端测试 | 中 |
| 第四阶段 | 完善错误处理与日志输出 | 中 |
| 第四阶段 | 编写测试用例 | 低 |
| 第五阶段 | 发布到 PyPI | 低 |

---

*musigate 实现报告 · v2.0 · 2026-04-05*
