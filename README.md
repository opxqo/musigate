# 🎵 musigate

**YAML 驱动的 Telegram Bot 交互引擎 —— 手写或 AI Agent 自动生成配置，轻松接入任意 Telegram 机器人。**

<p align="center">
  <code>pip install musigate</code> → <code>musigate download "Numb" --bot music163</code> → 🎧
</p>

---

## 它是什么

musigate 是一个 Python CLI 工具，通过**声明式 YAML 配置**与 Telegram Bot 交互并自动下载内容（音乐是首个应用场景）。不需要写 Python 代码——新增一个 Bot 只需写一个 YAML 文件，定义「发什么消息、等什么回复、点什么按钮、下什么文件」。

```
用户输入: musigate download "Numb" --bot music163
                    │
                    ▼
┌──────────────────────────────────────────────┐
│  CLI (cli.py)                                 │
│  解析命令行参数 → 构建请求上下文               │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Engine (engine.py)                           │
│  加载 Bot YAML → 初始化执行器 → 驱动流程       │
│  支持自动重试 (retry)                         │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Executor (executor.py)                      │
│  按步骤依次执行:                              │
│  send_message → wait_response                │
│  → click_button → download                   │
│  支持 branch / extract / respond_* 等动作     │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────┐    ┌──────────────────┐
│  Listener        │    │  Downloader      │
│  监听 Bot 回复    │    │  保存文件到本地    │
│  解析音频/按钮/文本│    │  显示进度和速度   │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
   Telegram Bot API           本地文件系统
```

## ✨ 特性

- **📝 零代码适配** — 每个 Bot 一个 YAML 文件，定义 `send → wait → click → download` 的交互链路
- **🤖 多 Bot 支持** — 已内置 Music163、MusicV1 适配，切换只需 `--bot xxx`
- **🎯 智能选择** — 编号精确选择 (`--pick N`)、歌名模糊匹配 (`match_title`)、编号+名称混合匹配 (`match_text_index`)
- **⚡ 自动重试** — `wait_response` 步骤支持可配置的重试次数，应对网络抖动
- **📦 开箱即用** — `pip install` 安装，一条命令登录、搜索、下载
- **📊 JSON 输出** — 全局 `--json` 标志，方便集成到脚本和其他工具链
- **🔗 链接下载** — 支持 `url` 命令通过音乐链接直接触发下载
- **🧩 可扩展** — 支持外部 Bot 目录、自定义配置文件路径、环境变量全覆盖

## 快速开始

### 安装

```bash
pip install -U musigate==0.1.0a4
```

或从源码开发安装：

```bash
git clone https://github.com/opxqo/musigate.git
cd musigate
pip install -e ".[dev]"
```

### 登录（零配置）

不需要手动创建 `.env` 或编辑任何配置文件。直接运行：

```bash
musigate login
```

首次登录会交互式引导你完成以下步骤：

#### 第一步：获取 Telegram API 凭据

如果还没有 API ID 和 API Hash，按以下步骤获取（只需一次）：

1. 在浏览器打开 [https://my.telegram.org](https://my.telegram.org)
2. 输入你的**手机号**（带国际区号，如 `+8613800138000`）
3. Telegram 会发送一个**验证码**到你的 Telegram 客户端（不是短信），在网页输入
4. 登录成功后，点击 **API development tools**
5. 填写应用信息（随便填即可）：
   - **App title**: `musigate`（或任意名称）
   - **Short name**: `musigate`（或任意短名称）
   - **URL**: 留空
- **Platform**: 选 `Other`
   - **Description**: 可选填，如 `Personal use`
6. 点击 **Create**，页面会显示两个值：
   - **api_id**: 一串数字，类似 `12345678`
   - **api_hash**: 一串字母数字混合字符串，类似 `abcdef1234567890abcdef`
7. **保存好这两个值**

#### 第二步：运行 login 命令

拿到 api_id 和 api_hash 后：

```bash
musigate login
```

命令会自动提示你：
1. 输入 **API ID**
2. 输入 **API Hash** → 输入后**自动保存到 `~/.musigate/.env`**（后续所有命令自动读取）
3. 输入**手机号**和**验证码** → 完成 Telegram 登录

整个过程只需这一条命令，之后搜索、下载等操作都复用已保存的 session。

> 💡 也可以跳过交互提示，直接通过命令行参数传入凭据：
> ```bash
> musigate login --api-id 12345678 --api-hash abcdef1234567890abcdef
> ```
>
> 🔄 切换账号（多账号场景）：
> ```bash
> musigate login --session-name another_account
> ```

### 高级配置（可选）

大部分用户不需要手动配置。如果需要自定义，支持以下方式：

**环境变量**（保存到 `~/.musigate/.env`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TELEGRAM_API_ID` | Telegram API ID | 由 `login` 命令自动填写 |
| `TELEGRAM_API_HASH` | Telegram API Hash | 由 `login` 命令自动填写 |
| `TELEGRAM_SESSION_NAME` | Session 文件名 | `musigate` |
| `TELEGRAM_PROXY_ENABLED` | 是否启用代理 | `false` |
| `TELEGRAM_PROXY_TYPE` | 代理类型 (`socks5` / `http`) | `socks5` |
| `TELEGRAM_PROXY_HOST` | 代理地址 | `127.0.0.1` |
| `TELEGRAM_PROXY_PORT` | 代理端口 | `7897` |
| `MUSIGATE_HOME` | 自定义数据目录（替代 `~/.musigate`） | — |
| `MUSIGATE_SETTINGS_FILE` | 自定义 settings.yaml 路径 | — |

**YAML 配置文件**：可放置在 `./config/settings.yaml`、项目根目录 `config/settings.yaml`，或打包资源中。

### 搜索 & 下载

```bash
# 搜索歌曲（不下载）
musigate search "周杰伦" --bot music163

# 智能匹配下载（自动选最接近的结果）
musigate download "Numb" --bot music163

# 按搜索结果编号精确下载
musigate download "海底" --bot music_v1 --pick 2

# 指定 music_v1 搜索平台
musigate search "海底" --bot music_v1 --source qq
musigate download "海底" --bot music_v1 --source netease --pick 1

# 通过链接下载
musigate url "https://music.163.com/song?id=xxx" --bot music163

# 下载到自定义目录
musigate download "Numb" --bot music163 --output ./my_music

# JSON 格式输出（方便集成到其他工具）
musigate search "Numb" --bot music163 --json
musigate download "Numb" --bot music163 --json

# 查看所有可用 Bot
musigate list-bots

# 测试 Bot 配置是否正确
musigate test --bot music163

# 退出登录
musigate logout
```

## 内置 Bot

| 名称 | Bot 账号 | 说明 |
|------|----------|------|
| `music163` | @Music163bot | 网易云歌曲搜索与下载 |
| `music_v1` | @music_v1bot | 音乐搜索与下载机器人 |

## Bot 适配指南

### 新增一个 Bot

只需在 `bots/` 目录创建一个 YAML 文件。以下是完整的 Music163 配置示例：

```yaml
name: Music163
bot_username: "@Music163bot"
description: "网易云歌曲下载机器人"

settings:
  timeout: 20    # 单步等待超时(秒)
  retry: 2       # wait_response 失败重试次数

commands:
  download:
    steps:
      - action: send_message
        content: "/search {query}"

      - action: wait_response
        expect: inline_buttons    # 等待带内联按钮的回复
        timeout: 15

      - action: click_button
        strategy: match_text_index # 编号 + 歌名混合模糊匹配
        query: "{query}"

      - action: wait_response
        expect: audio_file         # 等待 Bot 返回音频文件
        timeout: 30

      - action: download
        output: "{artist}-{title}.{ext}"  # 输出文件名模板

  search:
    steps:
      - action: send_message
        content: "/search {query}"

      - action: wait_response
        expect: inline_buttons
        timeout: 15

      - action: respond_list       # 将结果返回给 CLI 展示
```

把上面的 YAML 保存为 `bots/my_bot.yaml`，然后就能用了：

```bash
musigate list-bots          # 会看到你的新 Bot
musigate test --bot my_bot  # 测试配置是否有效
musigate download "歌曲名" --bot my_bot
```

### 支持的操作 (Actions)

| Action | 说明 | 关键参数 |
|--------|------|----------|
| `send_message` | 向 Bot 发送文本消息 | `content` — 支持 `{query}`、`{title}` 等变量 |
| `wait_response` | 等待 Bot 回复 | `expect`: `inline_buttons` / `audio_file` / `text` / `document` / `any`; `timeout` |
| `click_button` | 点击内联按钮 | `strategy`: 选择策略; `query`: 匹配关键词 |
| `download` | 保存接收到的文件到本地 | `output`: 文件名模板 |
| `respond_list` | 将文本或按钮列表返回给 CLI 展示 | — |
| `respond_buttons` | 将原始按钮数据返回给调用方 | — |
| `branch` | 按条件走不同的子步骤 | `cases`: 条件分支列表 |
| `error` | 主动抛出错误并终止流程 | `message`: 错误信息模板 |

### 选择策略 (Strategies)

| Strategy | 适用场景 | 说明 |
|----------|---------|------|
| `first` | 固定选第一个 | 总是点击第一个按钮 |
| `last` | 固定选最后一个 | 总是点击最后一个按钮 |
| `match_index N` | 固定位置选择 | 直接点击第 N 个按钮（从 0 开始） |
| `match_title` | 按钮显示歌名 | 用相似度算法模糊匹配最接近的按钮文字 |
| `match_text_index` | 编号+名称混合列表 | 从回复文本解析编号列表，再按歌名相似度匹配 |

### 分支条件 (Branch / When)

```yaml
- action: branch
  cases:
    - when:
        type: audio_file          # 回复类型匹配
      steps:
        - action: download
          output: "{title}.{ext}"
    - when:
        contains: "暂无版权"      # 文本包含判断
      steps:
        - action: error
          message: "该歌曲暂无版权"
    - when:
        not_contains: "搜索结果"  # 文本不包含判断
      steps:
        - action: error
          message: "未找到搜索结果"
```

### 变量模板

在 `send_message` 的 `content` 和 `download` 的 `output` 中可以使用以下变量：

| 变量 | 来源 | 示例值 |
|------|------|--------|
| `{query}` | 用户输入的搜索关键词 | `"Numb"` |
| `{title}` | 音频文件的标题 | `"Numb"` |
| `{artist}` | 音频文件的表演者 | `"Linkin Park"` |
| `{ext}` | 音频文件扩展名 | `"mp3"` |
| `{duration}` | 音频时长（秒） | `"216"` |
| `{pick}` | 用户指定的编号 | `2` |
| `{extracted_data.xxx}` | 正则提取的自定义字段 | — |

## 项目结构

```
musigate/
├── bots/                        # 外部 Bot YAML 配置（每Bot一个文件）
│   ├── music163.yaml
│   └── music_v1.yaml
├── config/
│   └── settings.yaml            # 全局默认设置（proxy、输出目录等）
├── src/musigate/
│   ├── __init__.py              # 版本号导出
│   ├── cli.py                   # Typer CLI 入口（6个命令）
│   ├── gateway/
│   │   ├── engine.py            # 流程引擎（步骤编排 + 重试逻辑）
│   │   ├── executor.py          # 步骤执行器（9种 action）
│   │   └── selector.py          # 按钮选择策略（5种策略）
│   ├── telegram/
│   │   ├── auth.py              # 登录/登出/session 管理
│   │   ├── client.py            # Telethon 客户端封装
│   │   └── listener.py          # Bot 回复监听与解析（音频/按钮/文本/文档）
│   ├── adapters/
│   │   └── loader.py            # Bot YAML 加载器（Pydantic 校验）+ 多源查找
│   ├── utils/
│   │   ├── config.py            # 设置加载（env + yaml + defaults 三级合并）
│   │   ├── downloader.py        # 文件下载（进度回调 + 速度/ETA 计算）
│   │   └── helper.py            # 模板渲染 / 文件名清理 / 目录创建
│   └── resources/
│       ├── __init__.py
│       ├── bots/                # 内置 Bot YAML（打包后从这里读取）
│       └── config/              # 内置默认 settings.yaml
├── tests/                       # pytest 测试
├── pyproject.toml
├── LICENSE                      # MIT
└── README.md
```

## 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Telegram 客户端 | [Telethon](https://telethon.dev/) | MTProto 异步客户端 |
| CLI 框架 | [Typer](https://typer.tiangolo.com/) | 命令行接口定义 |
| 终端美化 | [Rich](https://rich.readthedocs.io/) | 彩色输出、进度展示 |
| 配置解析 | PyYAML + [Pydantic](https://docs.pydantic.dev/) | YAML 校验与数据模型 |
| 环境变量 | [python-dotenv](https://github.com/theskumar/python-dotenv) | `.env` 文件加载 |
| 异步运行时 | asyncio (Python 3.10+) | 全链路异步 |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 构建分发包
python -m build
```

## License

[MIT](LICENSE)
