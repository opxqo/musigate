import asyncio
import json
import re
from typing import Any

import typer
from rich.console import Console

from musigate.adapters.loader import list_bots as list_bot_configs
from musigate.adapters.loader import load_bot
from musigate.gateway.engine import Engine
from musigate.telegram.auth import TelegramAuth
from musigate.telegram.client import Client
from musigate.utils.config import (
    build_telegram_proxy,
    load_settings,
    persist_env_values,
    resolve_env_file,
    resolve_session_name,
    validate_telegram_settings,
)

app = typer.Typer(no_args_is_help=True)
console = Console()


def _print_status(message: str, style: str = "white") -> None:
    console.print(message, style=style)


def _emit_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _compact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        compacted = {}
        for key, item in value.items():
            compacted_item = _compact_payload(item)
            if compacted_item is None or compacted_item == {} or compacted_item == []:
                continue
            compacted[key] = compacted_item
        return compacted

    if isinstance(value, list):
        return [
            item
            for item in (_compact_payload(entry) for entry in value)
            if item is not None and item != {} and item != []
        ]

    return value


def _build_client(settings: dict[str, Any]) -> Client:
    validate_telegram_settings(settings)
    return Client(
        api_id=settings["telegram"]["apiId"],
        api_hash=settings["telegram"]["apiHash"],
        session_name=resolve_session_name(settings["telegram"]["sessionName"]),
        proxy=build_telegram_proxy(settings),
    )


def _resolve_login_settings(
    settings: dict[str, Any],
    *,
    api_id: int | None,
    api_hash: str | None,
    session_name: str | None,
    save_credentials: bool,
) -> dict[str, Any]:
    telegram = settings.setdefault("telegram", {})
    prompted = False

    effective_api_id = api_id or telegram.get("apiId")
    if not effective_api_id:
        effective_api_id = typer.prompt("Telegram API ID", type=int)
        prompted = True

    effective_api_hash = api_hash or telegram.get("apiHash")
    if not effective_api_hash:
        effective_api_hash = typer.prompt("Telegram API hash").strip()
        prompted = True

    telegram["apiId"] = effective_api_id
    telegram["apiHash"] = effective_api_hash

    if session_name:
        telegram["sessionName"] = session_name

    if save_credentials and (prompted or api_id is not None or api_hash is not None or session_name):
        env_path = persist_env_values(
            {
                "TELEGRAM_API_ID": telegram["apiId"],
                "TELEGRAM_API_HASH": telegram["apiHash"],
                "TELEGRAM_SESSION_NAME": telegram.get("sessionName", "musigate"),
            }
        )
        if env_path == resolve_env_file():
            _print_status(f"OK: Saved Telegram credentials to {env_path}", "green")

    return settings


async def _run_engine_command(
    command: str,
    bot: str,
    include_context: bool = False,
    **kwargs: Any,
):
    settings = load_settings()
    bot_config = load_bot(bot)
    client = _build_client(settings)
    await client.connect()
    try:
        engine = Engine(bot_config, client)
        result = await engine._run_async(
            command,
            return_context=include_context,
            **kwargs,
        )
        return bot_config, result
    finally:
        await client.disconnect()


def _serialize_bot_config(bot_config: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": bot_config.get("name"),
        "bot_username": bot_config.get("bot_username"),
        "description": bot_config.get("description", ""),
        "version": bot_config.get("version"),
        "commands": sorted(bot_config.get("commands", {}).keys()),
    }


def _flatten_button_texts(buttons: list[list[dict[str, Any]]] | None) -> list[str]:
    if not buttons:
        return []
    return [
        button["text"]
        for row in buttons
        for button in row
        if button.get("text")
    ]


def _parse_search_results(
    raw_text: str,
    buttons: list[list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    button_texts = _flatten_button_texts(buttons)

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        entry: dict[str, Any] = {"text": stripped}
        match = re.match(r"^\s*(\d+)(?:[\.、。]|\s)\s*(.+?)\s*$", stripped)

        if match:
            index = int(match.group(1))
            content = match.group(2).strip()
            entry["index"] = index

            if str(index) in button_texts:
                entry["button"] = str(index)

            title_artist_match = re.match(r"^(?P<title>.+?)\s*-\s*(?P<artist>.+)$", content)
            if title_artist_match:
                entry["title"] = title_artist_match.group("title").strip()
                entry["artist"] = title_artist_match.group("artist").strip()
            else:
                entry["title"] = content
        elif len(button_texts) > len(results):
            entry["button"] = button_texts[len(results)]

        results.append(entry)

    return results


def _build_search_payload(
    bot_config: dict[str, Any],
    query: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    response = context.get("last_response") or {}
    raw_text = context.get("result") if isinstance(context.get("result"), str) else ""
    if not raw_text:
        raw_text = response.get("text", "")

    return _compact_payload(
        {
            "ok": True,
            "command": "search",
            "query": query,
            "bot": bot_config.get("name"),
            "bot_username": bot_config.get("bot_username"),
            "raw_text": raw_text,
            "results": _parse_search_results(raw_text, response.get("buttons")),
        }
    )


def _build_transfer_payload(
    command: str,
    bot_config: dict[str, Any],
    context: dict[str, Any],
    *,
    query: str | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    response = context.get("last_response") or {}

    return _compact_payload(
        {
            "ok": True,
            "command": command,
            "bot": bot_config.get("name"),
            "bot_username": bot_config.get("bot_username"),
            "query": query,
            "url": url,
            "selected_index": context.get("pick"),
            "output_dir": context.get("output"),
            "saved_path": context.get("result"),
            "filename": context.get("result_filename"),
            "track": {
                "title": response.get("title"),
                "artist": response.get("artist"),
                "ext": response.get("ext"),
                "duration": response.get("duration"),
                "mime_type": response.get("mime_type"),
                "size": response.get("size"),
                "file_name": response.get("file_name"),
                "message_text": response.get("text"),
            },
        }
    )


def _emit_command_error(
    command: str,
    error: Exception,
    *,
    bot: str | None = None,
    query: str | None = None,
    url: str | None = None,
) -> None:
    _emit_json(
        _compact_payload(
            {
                "ok": False,
                "command": command,
                "bot": bot,
                "query": query,
                "url": url,
                "error": str(error),
            }
        )
    )


@app.command()
def login(
    api_id: int | None = typer.Option(None, "--api-id", help="Telegram API ID"),
    api_hash: str | None = typer.Option(None, "--api-hash", help="Telegram API hash"),
    session_name: str | None = typer.Option(
        None,
        "--session-name",
        help="Session file name, defaults to musigate",
    ),
    save_credentials: bool = typer.Option(
        True,
        "--save/--no-save",
        help="Save entered Telegram credentials to .env in the current directory",
    ),
):
    """登录 Telegram 账号"""
    settings = load_settings()
    settings = _resolve_login_settings(
        settings,
        api_id=api_id,
        api_hash=api_hash,
        session_name=session_name,
        save_credentials=save_credentials,
    )
    validate_telegram_settings(settings)
    auth = TelegramAuth(
        api_id=settings["telegram"]["apiId"],
        api_hash=settings["telegram"]["apiHash"],
        session_name=resolve_session_name(settings["telegram"]["sessionName"]),
        proxy=build_telegram_proxy(settings),
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
        session_name=resolve_session_name(settings["telegram"]["sessionName"]),
        proxy=build_telegram_proxy(settings),
    )
    asyncio.run(auth.logout())


@app.command()
def download(
    query: str = typer.Argument(..., help="歌曲名或关键词"),
    bot: str = typer.Option(..., "--bot", "-b", help="机器人名称"),
    pick: int | None = typer.Option(None, "--pick", min=1, help="按搜索结果编号下载"),
    output: str | None = typer.Option(None, "--output", "-o", help="输出目录"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出结果"),
):
    """搜索并下载音乐"""
    try:
        settings = load_settings()
        target_output = output or settings["download"]["defaultOutput"]
        bot_config, result = asyncio.run(
            _run_engine_command(
                "download",
                bot,
                include_context=json_output,
                query=query,
                pick=pick,
                output=target_output,
                show_progress=not json_output,
            )
        )

        if json_output:
            _emit_json(_build_transfer_payload("download", bot_config, result, query=query))
            return

        _print_status(f"OK: 已连接 {bot_config['bot_username']}", "blue")
        _print_status(f'OK: 开始搜索 "{query}"', "blue")
        if pick is not None:
            _print_status(f"OK: 指定下载第 {pick} 条结果", "blue")
        if result:
            _print_status(f"OK: 下载完成，已保存到 {result}", "green")
        else:
            _print_status("WARN: 流程执行完毕，但未返回文件", "yellow")
    except Exception as error:
        if json_output:
            _emit_command_error("download", error, bot=bot, query=query)
        else:
            _print_status(f"ERROR: {error}", "red")
        raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="歌曲名或关键词"),
    bot: str = typer.Option(..., "--bot", "-b", help="机器人名称"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出结果"),
):
    """仅搜索，返回结果列表"""
    try:
        bot_config, result = asyncio.run(
            _run_engine_command(
                "search",
                bot,
                include_context=json_output,
                query=query,
            )
        )

        if json_output:
            _emit_json(_build_search_payload(bot_config, query, result))
            return

        _print_status(f"OK: 已连接 {bot_config['bot_username']}", "blue")
        _print_status(f'OK: 开始搜索 "{query}"', "blue")
        if result:
            _print_status("OK: 搜索结果:", "green")
            if isinstance(result, str):
                console.print(result)
            else:
                for row in result:
                    for button in row:
                        console.print(f"  - {button['text']}")
        else:
            _print_status("WARN: 未找到结果", "yellow")
    except Exception as error:
        if json_output:
            _emit_command_error("search", error, bot=bot, query=query)
        else:
            _print_status(f"ERROR: {error}", "red")
        raise typer.Exit(code=1)


@app.command()
def url(
    url: str = typer.Argument(..., help="音乐链接"),
    bot: str = typer.Option(..., "--bot", "-b", help="机器人名称"),
    output: str | None = typer.Option(None, "--output", "-o", help="输出目录"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出结果"),
):
    """通过链接直接下载"""
    try:
        settings = load_settings()
        target_output = output or settings["download"]["defaultOutput"]
        bot_config, result = asyncio.run(
            _run_engine_command(
                "url",
                bot,
                include_context=json_output,
                url=url,
                output=target_output,
                show_progress=not json_output,
            )
        )

        if json_output:
            _emit_json(_build_transfer_payload("url", bot_config, result, url=url))
            return

        _print_status(f"OK: 已连接 {bot_config['bot_username']}", "blue")
        _print_status(f'OK: 开始处理链接 "{url}"', "blue")
        if result:
            _print_status(f"OK: 下载完成，已保存到 {result}", "green")
        else:
            _print_status("WARN: 流程执行完毕，但未返回文件", "yellow")
    except Exception as error:
        if json_output:
            _emit_command_error("url", error, bot=bot, url=url)
        else:
            _print_status(f"ERROR: {error}", "red")
        raise typer.Exit(code=1)


@app.command("list-bots")
def list_bots(
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出结果"),
):
    """列出所有可用机器人"""
    configs = list_bot_configs()

    if json_output:
        _emit_json(
            {
                "ok": True,
                "command": "list-bots",
                "count": len(configs),
                "bots": [_serialize_bot_config(config) for config in configs],
            }
        )
        return

    if not configs:
        _print_status("WARN: 暂无可用机器人配置", "yellow")
        return

    console.print("可用机器人列表:", style="bold")
    for bot_config in configs:
        console.print(
            f"  - {bot_config.get('name', 'Unknown')} ({bot_config.get('bot_username', 'Unknown')})"
        )
        if bot_config.get("description"):
            console.print(f"    {bot_config['description']}", style="dim")


@app.command()
def test(
    bot: str = typer.Option(..., "--bot", "-b", help="机器人名称"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出结果"),
):
    """测试机器人是否可用"""
    try:
        bot_config = load_bot(bot)

        if json_output:
            _emit_json(
                {
                    "ok": True,
                    "command": "test",
                    "bot": bot,
                    **_serialize_bot_config(bot_config),
                }
            )
            return

        _print_status(f"OK: 正在测试 {bot}", "blue")
        _print_status(f"OK: 配置文件 {bot}.yaml 格式正确", "green")
        console.print(f"  - 机器人名: {bot_config['name']}")
        console.print(f"  - 账号: {bot_config['bot_username']}")
        console.print(f"  - 支持的命令: {', '.join(bot_config['commands'].keys())}")
    except Exception as error:
        if json_output:
            _emit_command_error("test", error, bot=bot)
        else:
            _print_status(f"ERROR: 测试失败: {error}", "red")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
