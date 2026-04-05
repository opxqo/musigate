# musigate 命令映射系统设计与实现方案

**文档版本：** v1.0  
**日期：** 2026-04-05  
**依据：** @Music163bot 真实交互数据

---

## 当前实现对齐说明

- 当前项目继续采用 YAML 驱动架构，不引入 LLM 参与命令执行。
- `@Music163bot` 的搜索结果继续按 `inline_buttons` 处理，并在响应中保留 `text` 字段用于展示歌曲列表。
- Music163 的结果选择保留 `match_text_index` 逻辑：先从文本列表中找最相近的编号，再点击对应数字按钮，不退化为固定点击第一个结果。
- `search` 命令吸收 `respond_list` 思路，优先把搜索文本直接返回给 CLI 展示。
- `text_with_buttons` 暂不作为独立强制类型落地；如果后续接入更多 bot，再考虑作为 `inline_buttons` 的细分或别名。

---

## 一、背景与目标

命令映射系统是 musigate 的核心，负责将用户的一级 CLI 命令翻译成针对具体 Telegram 机器人的二级操作序列。

**设计目标：**

- 支持四种真实交互场景的 YAML 描述
- 引擎稳定执行，不依赖 LLM
- 新增机器人只需写 YAML，不改代码
- 基于真实抓取数据，有据可查

---

## 二、真实数据分析（@Music163bot）

### 2.1 交互模式确认

通过对 `@Music163bot` 的真实数据抓取，确认其交互流程如下：

```
发送 /search Numb
      ↓
返回文字列表 + 数字按钮（同一条消息）
      ↓
点击数字按钮（如 "1"，data: "music 16686599"）
      ↓
返回音频文件消息（含 Document 媒体）
```

**重要发现：直接发送 "Numb" 返回空**，说明该机器人只响应 `/search` 命令，不响应普通消息。

### 2.2 第一步返回数据结构

```
message.message（文字内容）：
  1.「Numb」 - Linkin Park
  2.「NUMB」 - XXXTENTACION
  3.「NUMB」 - XXXTENTACION
  4.「Numb  (Live)」 - Linkin Park
  5.「Numb (8D Audio)」 - 8D Tunes
  ...

message.reply_markup.rows[0].buttons（数字按钮）：
  { text: "1", data: "music 16686599" }
  { text: "2", data: "music 545350938" }
  { text: "3", data: "music 2644446805" }
  ...（共8个，对应8条搜索结果）
```

**关键特征：文字列表和数字按钮在同一条消息里同时返回。**

### 2.3 第二步返回数据结构

```
message.message（文字内容）：
  「Numb」- Linkin Park
  专辑: Meteora
  #网易云音乐 #flac 23.88MB 1066.02kbps
  via @Music163bot

message.media.document：
  mime_type:  "audio/x-flac"
  size:       25043574 字节（23.88MB）
  attributes:
    DocumentAttributeAudio:
      title:     "Numb"
      performer: "Linkin Park"
      duration:  187（秒）
    DocumentAttributeFilename:
      file_name: "Linkin Park - Numb.flac"
```

### 2.4 数据结构对照表

| 字段路径 | 值 | 用途 |
|---|---|---|
| `message.message` | 歌曲列表文字 | 展示搜索结果 |
| `reply_markup.rows[0].buttons[n].text` | `"1"` ~ `"8"` | 按钮显示文字 |
| `reply_markup.rows[0].buttons[n].data` | `"music 16686599"` | 点击时发送的数据 |
| `media.document.mime_type` | `"audio/x-flac"` | 判断是否为音频 |
| `media.document.attributes[0].title` | `"Numb"` | 文件名模板变量 |
| `media.document.attributes[0].performer` | `"Linkin Park"` | 文件名模板变量 |
| `media.document.attributes[1].file_name` | `"Linkin Park - Numb.flac"` | 原始文件名 |

---

## 三、消息响应类型规范

基于真实数据，定义以下五种标准响应类型：

### 3.1 响应类型定义

**类型一：audio_file（音频文件）**

```
判断条件：
  message.media._  == "MessageMediaDocument"
  document.mime_type in ["audio/mpeg", "audio/x-flac", "audio/ogg", "audio/mp4"]

提取字段：
  title     ← document.attributes[DocumentAttributeAudio].title
  performer ← document.attributes[DocumentAttributeAudio].performer
  duration  ← document.attributes[DocumentAttributeAudio].duration
  file_name ← document.attributes[DocumentAttributeFilename].file_name
  ext       ← mime_type 推导（audio/x-flac → flac，audio/mpeg → mp3）
  size      ← document.size
  media     ← message.media（用于下载）
```

**类型二：inline_buttons（纯按钮）**

```
判断条件：
  message.message 为空或很短
  message.reply_markup 存在
  message.media 为 null

提取字段：
  buttons ← reply_markup.rows 展平为二维列表
```

**类型三：text_with_buttons（文字+按钮，Music163bot 属于此类）**

```
判断条件：
  message.message 非空（超过20字符）
  message.reply_markup 存在
  message.media 为 null

提取字段：
  text    ← message.message（歌曲列表文字）
  buttons ← reply_markup.rows 展平为二维列表
```

**类型四：text_message（纯文字）**

```
判断条件：
  message.message 非空
  message.reply_markup 为 null 或不存在
  message.media 为 null

提取字段：
  text ← message.message
```

**类型五：any（接受任意类型，用于条件分支）**

```
判断条件：无限制，收到任何消息都匹配
提取字段：同上各类型，自动识别
```

### 3.2 listener.py 解析逻辑

```python
def _parse(self, message, expect: str) -> dict | None:
    """
    解析 Telethon 消息，返回标准化的响应字典
    """
    has_text    = bool(message.message and len(message.message) > 20)
    has_buttons = bool(message.reply_markup)
    has_audio   = (
        message.media and
        hasattr(message.media, "document") and
        message.media.document.mime_type.startswith("audio/")
    )

    # 识别实际类型
    if has_audio:
        actual_type = "audio_file"
    elif has_text and has_buttons:
        actual_type = "text_with_buttons"
    elif has_buttons:
        actual_type = "inline_buttons"
    elif has_text:
        actual_type = "text_message"
    else:
        return None

    # expect: any 直接通过
    if expect != "any" and expect != actual_type:
        return None

    # 按类型提取数据
    if actual_type == "audio_file":
        return self._extract_audio(message)

    elif actual_type in ("text_with_buttons", "inline_buttons"):
        return self._extract_buttons(message, actual_type)

    elif actual_type == "text_message":
        return {"type": "text_message", "text": message.message}

def _extract_audio(self, message) -> dict:
    doc = message.media.document
    audio_attr = next(
        (a for a in doc.attributes if a.__class__.__name__ == "DocumentAttributeAudio"),
        None
    )
    file_attr = next(
        (a for a in doc.attributes if a.__class__.__name__ == "DocumentAttributeFilename"),
        None
    )
    ext_map = {
        "audio/x-flac": "flac",
        "audio/mpeg":   "mp3",
        "audio/ogg":    "ogg",
        "audio/mp4":    "m4a",
    }
    return {
        "type":      "audio_file",
        "title":     getattr(audio_attr, "title", "unknown"),
        "performer": getattr(audio_attr, "performer", "unknown"),
        "duration":  getattr(audio_attr, "duration", 0),
        "file_name": getattr(file_attr, "file_name", "music"),
        "ext":       ext_map.get(doc.mime_type, "mp3"),
        "size":      doc.size,
        "media":     message.media,
    }

def _extract_buttons(self, message, actual_type: str) -> dict:
    rows = message.reply_markup.rows
    buttons = [
        [
            {
                "text":     btn.text,
                "data":     getattr(btn, "data", None),
                "_message": message,
            }
            for btn in row.buttons
        ]
        for row in rows
    ]
    return {
        "type":    actual_type,
        "text":    message.message or "",
        "buttons": buttons,
    }
```

---

## 四、YAML 命令规范

### 4.1 完整字段说明

```yaml
name: ""                  # 机器人显示名称
bot_username: ""          # Telegram 用户名（含@）
description: ""           # 功能描述
version: "1.0"            # 适配器版本

settings:
  timeout: 15             # 默认每步超时（秒）
  retry: 2                # 失败重试次数
  step_delay: 0.5         # 每步之间的延迟（秒，防风控）

commands:
  <command_name>:         # 一级命令名
    steps:
      - action: <action>  # 二级命令
        <参数>: <值>
```

### 4.2 所有支持的 action

| action | 说明 | 必填参数 | 可选参数 |
|---|---|---|---|
| `send_message` | 发送文字消息给机器人 | `content` | — |
| `wait_response` | 等待机器人回复 | `expect` | `timeout` |
| `click_button` | 点击内联按钮 | `strategy` | `query`、`index` |
| `extract` | 从文字中提取数据 | `pattern`、`save_as` | `source` |
| `branch` | 条件分支 | `cases` | — |
| `download` | 下载音频文件 | — | `output` |
| `respond_list` | 将搜索结果返回给用户 | — | — |
| `error` | 主动抛出错误终止执行 | `message` | — |

### 4.3 click_button 策略详解

| strategy | 说明 | 适用场景 |
|---|---|---|
| `first` | 第一个按钮 | 结果已排序，取最相关 |
| `last` | 最后一个按钮 | 特殊布局 |
| `match_title` | 相似度最高的按钮 | 按钮文字是歌名 |
| `match_text_index` | 从返回文本中匹配最相近编号，再点击对应数字按钮 | 按钮文字是编号，文本里才有歌名 |
| `match_index` | 第 N 个按钮（0起始） | 固定位置，如 Music163bot 点 "1" |

**Music163bot 的按钮特殊性：** 按钮文字是纯数字 `"1"-"8"`，不是歌名，因此当前项目使用 `match_text_index`，根据文本列表和查询词自动定位最匹配的编号，而不是固定点击第一个按钮。

---

## 五、四种场景 YAML 完整示例

### 5.1 场景一：简单直发型

```yaml
# bots/musichunter.yaml
name: MusicsHunter
bot_username: "@MusicsHunterBot"
description: "发送歌名直接返回音频文件，支持 MP3/FLAC"
version: "1.0"

settings:
  timeout: 30
  retry: 2
  step_delay: 1.0

commands:

  download:
    steps:
      - action: send_message
        content: "{query}"

      - action: wait_response
        expect: audio_file
        timeout: 30

      - action: download
        output: "{performer}-{title}.{ext}"

  url:
    steps:
      - action: send_message
        content: "{url}"

      - action: wait_response
        expect: audio_file
        timeout: 30

      - action: download
        output: "{performer}-{title}.{ext}"
```

### 5.2 场景二：按钮选择型

```yaml
# bots/vkmusic.yaml
name: VKMusic
bot_username: "@VKM_bot"
description: "VK 音乐库，搜索返回歌名按钮列表"
version: "1.0"

settings:
  timeout: 15
  retry: 2
  step_delay: 0.5

commands:

  download:
    steps:
      - action: send_message
        content: "{query}"

      - action: wait_response
        expect: inline_buttons
        timeout: 10

      - action: click_button
        strategy: match_title    # 按钮文字是歌名，用相似度匹配
        query: "{query}"

      - action: wait_response
        expect: audio_file
        timeout: 30

      - action: download
        output: "{performer}-{title}.{ext}"

  search:
    steps:
      - action: send_message
        content: "{query}"

      - action: wait_response
        expect: inline_buttons
        timeout: 10

      - action: respond_list
```

### 5.3 场景三：多轮对话型（基于 Music163bot 真实数据）

```yaml
# bots/music163.yaml
name: Music163
bot_username: "@Music163bot"
description: "网易云音乐，FLAC 高音质，需用 /search 命令"
version: "1.0"

settings:
  timeout: 15
  retry: 2
  step_delay: 1.0

commands:

  download:
    steps:
      - action: send_message
        content: "/search {query}"       # 必须用 /search，直接发歌名无响应

      - action: wait_response
        expect: inline_buttons           # 当前实现统一按 inline_buttons 处理，并保留 text
        timeout: 10

      - action: click_button
        strategy: match_text_index       # 结合文本列表与 query 自动选择最相关编号
        query: "{query}"

      - action: wait_response
        expect: audio_file               # 返回 audio/x-flac 文件
        timeout: 30

      - action: download
        output: "{performer}-{title}.{ext}"

  search:
    steps:
      - action: send_message
        content: "/search {query}"

      - action: wait_response
        expect: inline_buttons
        timeout: 10

      - action: respond_list             # 直接把 text 返回给 CLI 展示
```

### 5.4 场景四：条件分支型

```yaml
# bots/smartbot.yaml
name: SmartBot
bot_username: "@smartbot"
description: "响应类型不固定，自动分支处理"
version: "1.0"

settings:
  timeout: 15
  retry: 2
  step_delay: 0.5

commands:

  download:
    steps:
      - action: send_message
        content: "{query}"

      - action: wait_response
        expect: any                       # 不限定类型
        timeout: 10

      - action: branch
        cases:

          - when:
              type: audio_file            # 直接返回了文件
            steps:
              - action: download
                output: "{performer}-{title}.{ext}"

          - when:
              type: inline_buttons        # 返回纯按钮
            steps:
              - action: click_button
                strategy: match_title
                query: "{query}"
              - action: wait_response
                expect: audio_file
                timeout: 30
              - action: download
                output: "{performer}-{title}.{ext}"

          - when:
              type: text_with_buttons     # 文字+按钮
            steps:
              - action: click_button
                strategy: match_index
                index: 0
              - action: wait_response
                expect: audio_file
                timeout: 30
              - action: download
                output: "{performer}-{title}.{ext}"

          - when:
              type: text_message
              contains: "未找到"           # 明确的错误消息
            steps:
              - action: error
                message: "未找到歌曲: {query}"

          - when:
              type: text_message
              not_contains: "未找到"       # 文字列表（无按钮的机器人）
            steps:
              - action: send_message
                content: "1"
              - action: wait_response
                expect: audio_file
                timeout: 30
              - action: download
                output: "{performer}-{title}.{ext}"
```

---

## 六、引擎核心实现

### 6.1 engine.py

```python
"""
gateway/engine.py
核心规则引擎：读取 YAML steps，按顺序编排执行
"""
import asyncio
from musigate.gateway.executor import Executor


class Engine:
    def __init__(self, bot_config: dict, client, listener):
        self.config   = bot_config
        self.executor = Executor(bot_config, client, listener)

    def run(self, command: str, **kwargs) -> dict:
        return asyncio.run(self._run_async(command, **kwargs))

    async def _run_async(self, command: str, **kwargs) -> dict:
        command_def = self.config["commands"].get(command)
        if not command_def:
            raise ValueError(
                f"机器人 {self.config['name']} 不支持命令: {command}\n"
                f"可用命令: {list(self.config['commands'].keys())}"
            )

        context = {
            "query":         kwargs.get("query", ""),
            "url":           kwargs.get("url", ""),
            "output":        kwargs.get("output", "./downloads"),
            "lastResponse":  None,
            "extractedData": {},
            "result":        None,
        }

        await self._run_steps(command_def["steps"], context)
        return context

    async def _run_steps(self, steps: list, context: dict):
        """线性执行 steps，遇到 branch 递归处理"""
        delay = self.config.get("settings", {}).get("step_delay", 0.5)

        for step in steps:
            await self.executor.run(step, context)
            if delay > 0:
                await asyncio.sleep(delay)
```

### 6.2 executor.py

```python
"""
gateway/executor.py
执行每个具体的 action
"""
import re
from musigate.gateway.selector import Selector
from musigate.utils.helper import render_template
from musigate.utils.downloader import Downloader
from rich.console import Console

console = Console()


class Executor:
    def __init__(self, config: dict, client, listener):
        self.config   = config
        self.client   = client
        self.listener = listener
        self.selector = Selector()
        self.downloader = Downloader()

    async def run(self, step: dict, context: dict):
        action = step["action"]

        if action == "send_message":
            await self._send_message(step, context)

        elif action == "wait_response":
            await self._wait_response(step, context)

        elif action == "click_button":
            await self._click_button(step, context)

        elif action == "extract":
            self._extract(step, context)

        elif action == "branch":
            await self._branch(step, context)

        elif action == "download":
            await self._download(step, context)

        elif action == "respond_list":
            self._respond_list(context)

        elif action == "error":
            msg = render_template(step["message"], context)
            raise RuntimeError(msg)

        else:
            raise ValueError(f"未知 action: {action}")

    # ── 各 action 实现 ─────────────────────────────

    async def _send_message(self, step: dict, context: dict):
        content = render_template(step["content"], context)
        console.print(f"[dim]→ 发送: {content}[/dim]")
        await self.client.send_message(self.config["bot_username"], content)

    async def _wait_response(self, step: dict, context: dict):
        expect  = step["expect"]
        timeout = step.get("timeout", self.config["settings"].get("timeout", 15))
        retry   = self.config["settings"].get("retry", 2)
        console.print(f"[dim]→ 等待响应: {expect}（最多 {timeout}s）[/dim]")

        for attempt in range(retry + 1):
            try:
                response = await self.listener.wait(expect=expect, timeout=timeout)
                context["lastResponse"] = response
                return
            except TimeoutError:
                if attempt < retry:
                    console.print(f"[yellow]⚠ 超时，第 {attempt + 1} 次重试...[/yellow]")
                else:
                    raise TimeoutError(
                        f"等待 {expect} 超时，已重试 {retry} 次"
                    )

    async def _click_button(self, step: dict, context: dict):
        response = context.get("lastResponse")
        if not response or "buttons" not in response:
            raise RuntimeError("click_button: 上一步没有返回按钮")

        strategy = step["strategy"]
        query    = render_template(step.get("query", context.get("query", "")), context)
        index    = step.get("index", 0)

        button = self.selector.select(
            buttons=response["buttons"],
            strategy=strategy,
            query=query,
            index=index,
        )
        console.print(f"[dim]→ 点击按钮: {button['text']}[/dim]")
        await self.client.click_button(button)

    def _extract(self, step: dict, context: dict):
        source   = step.get("source", "lastResponse.text")
        pattern  = step["pattern"]
        save_as  = step["save_as"]

        # 取数据源
        if source == "lastResponse.text":
            text = context.get("lastResponse", {}).get("text", "")
        else:
            text = context.get(source, "")

        matches = re.findall(pattern, text, re.MULTILINE)
        context["extractedData"][save_as] = matches
        console.print(f"[dim]→ 提取 {save_as}: {matches[:3]}...[/dim]")

    async def _branch(self, step: dict, context: dict):
        response = context.get("lastResponse", {})
        resp_type = response.get("type", "")
        resp_text = response.get("text", "")

        for case in step["cases"]:
            when = case["when"]

            # 类型匹配
            if when.get("type") and when["type"] != resp_type:
                continue

            # contains 匹配
            if "contains" in when and when["contains"] not in resp_text:
                continue

            # not_contains 匹配
            if "not_contains" in when and when["not_contains"] in resp_text:
                continue

            # 命中分支，执行其 steps
            console.print(f"[dim]→ 命中分支: {when}[/dim]")
            from musigate.gateway.engine import Engine
            engine = Engine(self.config, self.client, self.listener)
            await engine._run_steps(case["steps"], context)
            return

        raise RuntimeError(f"branch: 没有匹配的分支，响应类型为 {resp_type}")

    async def _download(self, step: dict, context: dict):
        response = context.get("lastResponse")
        if not response or response.get("type") != "audio_file":
            raise RuntimeError("download: 上一步没有返回音频文件")

        output_template = step.get("output", "{performer}-{title}.{ext}")
        filename = render_template(output_template, {**context, **response})
        output_dir = context.get("output", "./downloads")

        console.print(f"[dim]→ 下载: {filename}[/dim]")
        saved_path = await self.downloader.save(
            media=response["media"],
            client=self.client,
            output_dir=output_dir,
            filename=filename,
        )
        context["result"] = saved_path
        console.print(f"[green]✔ 已保存: {saved_path}[/green]")

    def _respond_list(self, context: dict):
        response = context.get("lastResponse", {})
        text = response.get("text", "（无结果）")
        console.print(f"\n[bold]搜索结果：[/bold]\n{text}\n")
```

### 6.3 selector.py

```python
"""
gateway/selector.py
按钮选择策略
"""
from difflib import SequenceMatcher


class Selector:
    def select(
        self,
        buttons: list[list[dict]],
        strategy: str,
        query: str = "",
        index: int = 0,
    ) -> dict:
        flat = [btn for row in buttons for btn in row]

        if not flat:
            raise RuntimeError("selector: 没有可用按钮")

        if strategy == "first":
            return flat[0]

        elif strategy == "last":
            return flat[-1]

        elif strategy == "match_title":
            return max(flat, key=lambda b: self._sim(b["text"], query))

        elif strategy == "match_index":
            if index >= len(flat):
                raise RuntimeError(
                    f"selector: match_index {index} 超出范围（共 {len(flat)} 个按钮）"
                )
            return flat[index]

        else:
            raise ValueError(f"selector: 未知策略 {strategy}")

    def _sim(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
```

### 6.4 helper.py（模板渲染）

```python
"""
utils/helper.py
模板变量渲染
"""
import re


def render_template(template: str, context: dict) -> str:
    """
    将 {variable} 替换为 context 中对应的值
    支持嵌套：context 中的值也可以是字典
    """
    def replacer(match):
        key = match.group(1)
        # 先从顶层找，再从 lastResponse 找
        val = context.get(key)
        if val is None and context.get("lastResponse"):
            val = context["lastResponse"].get(key)
        return str(val) if val is not None else match.group(0)

    return re.sub(r"\{(\w+)\}", replacer, template)
```

---

## 七、完整执行流程（基于 Music163bot）

```
用户执行：
  musigate download "Numb" --bot music163

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
engine 初始化 context
  query  = "Numb"
  output = "./downloads"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step 1: send_message
  render "/search {query}" → "/search Numb"
  → 发送给 @Music163bot

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step 2: wait_response（expect: text_with_buttons）
  listener 监听 @Music163bot 消息...
  收到消息：
    text: "1.「Numb」 - Linkin Park\n2.「NUMB」..."
    buttons: [["1","2","3","4","5","6","7","8"]]
  类型识别：has_text=True, has_buttons=True → text_with_buttons ✅
  context.lastResponse = { type, text, buttons }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step 3: click_button（strategy: match_index, index: 0）
  flat = ["1","2","3","4","5","6","7","8"]
  选择 flat[0] → 按钮 { text:"1", data:"music 16686599" }
  → 点击按钮

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step 4: wait_response（expect: audio_file）
  listener 监听 @Music163bot 消息...
  收到消息：
    media.document.mime_type = "audio/x-flac"
  类型识别：has_audio=True → audio_file ✅
  context.lastResponse = {
    type:      "audio_file"
    title:     "Numb"
    performer: "Linkin Park"
    ext:       "flac"
    size:      25043574
    media:     <MessageMediaDocument>
  }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step 5: download（output: "{performer}-{title}.{ext}"）
  render → "Linkin Park-Numb.flac"
  → 下载到 ./downloads/Linkin Park-Numb.flac
  context.result = "./downloads/Linkin Park-Numb.flac"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLI 输出：
  ✔ 搜索 "Numb"
  ✔ 点击按钮 "1"（Numb - Linkin Park）
  ✔ 下载完成 23.88MB
  ✔ 已保存到 ./downloads/Linkin Park-Numb.flac
```

---

## 八、错误处理机制

### 8.1 错误类型与处理方式

| 错误场景 | 触发条件 | 处理方式 |
|---|---|---|
| wait_response 超时 | 超过 timeout 秒无响应 | 按 retry 次数重试，仍失败抛出 TimeoutError |
| expect 类型不匹配 | 返回类型与 expect 不符 | listener 返回 None，wait 继续等待直到超时 |
| click_button 无按钮 | lastResponse 无 buttons | 抛出 RuntimeError |
| match_index 越界 | index 超过按钮数量 | 抛出 RuntimeError，提示实际按钮数 |
| branch 无匹配 | 所有 cases 都不匹配 | 抛出 RuntimeError，报告响应类型 |
| download 无文件 | lastResponse 不是 audio_file | 抛出 RuntimeError |
| YAML 格式错误 | Pydantic 校验失败 | 报告具体字段和错误原因 |
| 机器人无响应 | /start 发送后无回复 | 提示检查机器人是否可用 |

### 8.2 重试机制

```python
# wait_response 内置重试
for attempt in range(retry + 1):
    try:
        response = await self.listener.wait(expect, timeout)
        return
    except TimeoutError:
        if attempt < retry:
            console.print(f"⚠ 超时，第 {attempt+1} 次重试...")
        else:
            raise
```

---

## 九、开发顺序建议

| 顺序 | 模块 | 说明 |
|---|---|---|
| 1 | `utils/helper.py` | 模板渲染，无依赖，最先实现 |
| 2 | `adapters/loader.py` | YAML 加载与 Pydantic 校验 |
| 3 | `telegram/client.py` | Telethon 连接封装 |
| 4 | `telegram/listener.py` | 消息监听与类型识别（核心） |
| 5 | `gateway/selector.py` | 按钮选择策略 |
| 6 | `gateway/executor.py` | action 执行器 |
| 7 | `gateway/engine.py` | 引擎编排 |
| 8 | `cli.py` | CLI 入口接入 |
| 9 | `bots/music163.yaml` | 第一个真实机器人适配，端到端验证 |

---

*musigate 命令映射系统设计与实现方案 · v1.0 · 2026-04-05*
