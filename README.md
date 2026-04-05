# musigate

[English](#english) | [中文](#中文)

## English

`musigate` is a Python CLI for searching and downloading music through Telegram bots with a YAML-driven adapter system.

This release is an alpha build. The core CLI flow is working, but bot behavior still depends on upstream Telegram bots and may change over time.

### Install

From a published package:

```bash
pip install musigate
```

From a local wheel:

```bash
pip install dist/musigate-0.1.0a1-py3-none-any.whl
```

For development:

```bash
pip install -e .[dev]
```

### Setup

Copy `.env.example` to `.env`, then fill in your Telegram API credentials:

```bash
cp .env.example .env
```

Required values:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`

### Built-in Bots

- `music163`
- `music_v1`

### Usage

Login to Telegram:

```bash
musigate login
```

Search only:

```bash
musigate search "Numb" --bot music163
```

Download with smart matching:

```bash
musigate download "Numb" --bot music163
```

Download a specific numbered search result:

```bash
musigate download "海底" --bot music_v1 --pick 2
```

Write files to a custom directory:

```bash
musigate download "海底" --bot music_v1 --pick 2 --output ./downloads/favorites
```

Machine-readable JSON output:

```bash
musigate search "Numb" --bot music163 --json
musigate download "Numb" --bot music163 --json
musigate list-bots --json
```

Normal CLI downloads show periodic progress updates including speed and ETA.

## 中文

`musigate` 是一个 Python 命令行工具，用来通过 Telegram 机器人搜索和下载音乐，核心采用 YAML 驱动的适配器架构。

当前版本是 alpha 初版。CLI 主流程已经可用，但具体机器人的行为仍依赖上游 Telegram 机器人，后续可能会变化。

### 安装

从已发布的包安装：

```bash
pip install musigate
```

从本地 wheel 安装：

```bash
pip install dist/musigate-0.1.0a1-py3-none-any.whl
```

开发模式安装：

```bash
pip install -e .[dev]
```

### 配置

把 `.env.example` 复制为 `.env`，然后填入你的 Telegram API 凭据：

```bash
cp .env.example .env
```

必填项：

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`

### 内置 Bot

- `music163`
- `music_v1`

### 使用方式

登录 Telegram：

```bash
musigate login
```

仅搜索，不下载：

```bash
musigate search "Numb" --bot music163
```

按智能匹配下载：

```bash
musigate download "Numb" --bot music163
```

按搜索结果编号精确下载：

```bash
musigate download "海底" --bot music_v1 --pick 2
```

下载到自定义目录：

```bash
musigate download "海底" --bot music_v1 --pick 2 --output ./downloads/favorites
```

输出机器可读 JSON：

```bash
musigate search "Numb" --bot music163 --json
musigate download "Numb" --bot music163 --json
musigate list-bots --json
```

普通 CLI 下载模式会定期显示进度、速度和预计剩余时间。
