import pytest
from unittest.mock import AsyncMock, MagicMock
from musigate.gateway.engine import Engine

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.send_message = AsyncMock()
    client.click_button = AsyncMock()
    client.download_media = AsyncMock()
    client.client = MagicMock()
    return client

@pytest.mark.asyncio
async def test_engine_simple_download(mock_client, monkeypatch, tmp_path):
    bot_config = {
        "bot_username": "@testbot",
        "settings": {"timeout": 15, "retry": 2},
        "commands": {
            "download": {
                "steps": [
                    {"action": "send_message", "content": "{query}"},
                    {"action": "wait_response", "expect": "audio_file"},
                    {"action": "download", "output": "{title}.{ext}"}
                ]
            }
        }
    }

    mock_wait = AsyncMock(return_value={
        "type": "audio_file",
        "title": "Test Song",
        "ext": "mp3",
        "file": "mock_file_obj"
    })
    monkeypatch.setattr("musigate.gateway.executor.Listener.wait", mock_wait)

    engine = Engine(bot_config, mock_client)
    result = await engine._run_async("download", query="Test Song", output=str(tmp_path))

    assert mock_client.send_message.called
    assert mock_wait.called
    assert mock_client.download_media.called
    assert result.endswith("Test Song.mp3")

@pytest.mark.asyncio
async def test_engine_button_download(mock_client, monkeypatch, tmp_path):
    bot_config = {
        "bot_username": "@testbot",
        "settings": {"timeout": 15, "retry": 2},
        "commands": {
            "download": {
                "steps": [
                    {"action": "send_message", "content": "{query}"},
                    {"action": "wait_response", "expect": "inline_buttons"},
                    {"action": "click_button", "strategy": "first"},
                    {"action": "wait_response", "expect": "audio_file"},
                    {"action": "download", "output": "{title}.{ext}"}
                ]
            }
        }
    }

    mock_wait = AsyncMock(side_effect=[
        {
            "type": "inline_buttons",
            "text": "Choose:",
            "buttons": [[{"text": "Btn1", "data": "1", "_message": MagicMock()}]]
        },
        {
            "type": "audio_file",
            "title": "Btn1 Song",
            "ext": "mp3",
            "file": "mock_file_obj"
        }
    ])
    monkeypatch.setattr("musigate.gateway.executor.Listener.wait", mock_wait)

    engine = Engine(bot_config, mock_client)
    result = await engine._run_async("download", query="Test Song", output=str(tmp_path))

    assert mock_client.send_message.called
    assert mock_client.click_button.called
    assert mock_client.download_media.called
    assert result.endswith("Btn1 Song.mp3")


@pytest.mark.asyncio
async def test_engine_retries_wait_response(mock_client, monkeypatch, tmp_path):
    bot_config = {
        "bot_username": "@testbot",
        "settings": {"timeout": 15, "retry": 1},
        "commands": {
            "download": {
                "steps": [
                    {"action": "send_message", "content": "{query}"},
                    {"action": "wait_response", "expect": "audio_file"},
                    {"action": "download", "output": "{title}.{ext}"},
                ]
            }
        },
    }

    mock_wait = AsyncMock(side_effect=[
        TimeoutError("等待 audio_file 超时（15s）"),
        {
            "type": "audio_file",
            "title": "Retried Song",
            "ext": "mp3",
            "file": "mock_file_obj",
        },
    ])
    monkeypatch.setattr("musigate.gateway.executor.Listener.wait", mock_wait)

    engine = Engine(bot_config, mock_client)
    result = await engine._run_async("download", query="Retry Song", output=str(tmp_path))

    assert mock_wait.await_count == 2
    assert result.endswith("Retried Song.mp3")


@pytest.mark.asyncio
async def test_engine_extracts_text_for_follow_up_step(mock_client, monkeypatch, tmp_path):
    bot_config = {
        "bot_username": "@testbot",
        "settings": {"timeout": 15, "retry": 0},
        "commands": {
            "download": {
                "steps": [
                    {"action": "send_message", "content": "/search {query}"},
                    {
                        "action": "wait_response",
                        "expect": "text_message",
                        "extract": {"pattern": r"^(\d+)\.", "save_as": "choice"},
                    },
                    {"action": "send_message", "content": "{choice}"},
                    {"action": "wait_response", "expect": "audio_file"},
                    {"action": "download", "output": "{title}.{ext}"},
                ]
            }
        },
    }

    mock_wait = AsyncMock(side_effect=[
        {"type": "text_message", "text": "1. First Song\n2. Second Song"},
        {
            "type": "audio_file",
            "title": "Chosen Song",
            "ext": "mp3",
            "file": "mock_file_obj",
        },
    ])
    monkeypatch.setattr("musigate.gateway.executor.Listener.wait", mock_wait)

    engine = Engine(bot_config, mock_client)
    result = await engine._run_async("download", query="Chosen Song", output=str(tmp_path))

    assert mock_client.send_message.await_args_list[1].args[1] == "1"
    assert result.endswith("Chosen Song.mp3")


@pytest.mark.asyncio
async def test_engine_branch_download_path(mock_client, monkeypatch, tmp_path):
    bot_config = {
        "bot_username": "@testbot",
        "settings": {"timeout": 15, "retry": 0},
        "commands": {
            "download": {
                "steps": [
                    {"action": "send_message", "content": "{query}"},
                    {"action": "wait_response", "expect": "any"},
                    {
                        "action": "branch",
                        "cases": [
                            {
                                "when": {"type": "audio_file"},
                                "steps": [
                                    {"action": "download", "output": "{title}.{ext}"}
                                ],
                            }
                        ],
                    },
                ]
            }
        },
    }

    mock_wait = AsyncMock(return_value={
        "type": "audio_file",
        "title": "Direct Song",
        "ext": "mp3",
        "file": "mock_file_obj",
    })
    monkeypatch.setattr("musigate.gateway.executor.Listener.wait", mock_wait)

    engine = Engine(bot_config, mock_client)
    result = await engine._run_async("download", query="Direct Song", output=str(tmp_path))

    assert mock_client.download_media.called
    assert result.endswith("Direct Song.mp3")


@pytest.mark.asyncio
async def test_engine_respond_list_returns_search_text(mock_client, monkeypatch):
    bot_config = {
        "bot_username": "@testbot",
        "settings": {"timeout": 15, "retry": 0},
        "commands": {
            "search": {
                "steps": [
                    {"action": "send_message", "content": "/search {query}"},
                    {"action": "wait_response", "expect": "inline_buttons"},
                    {"action": "respond_list"},
                ]
            }
        },
    }

    mock_wait = AsyncMock(return_value={
        "type": "inline_buttons",
        "text": "1. Numb - Linkin Park\n2. Numb - Demo Artist",
        "buttons": [[{"text": "1", "data": "1", "_message": MagicMock()}]],
    })
    monkeypatch.setattr("musigate.gateway.executor.Listener.wait", mock_wait)

    engine = Engine(bot_config, mock_client)
    result = await engine._run_async("search", query="Numb")

    assert result == "1. Numb - Linkin Park\n2. Numb - Demo Artist"


@pytest.mark.asyncio
async def test_engine_return_context_uses_snake_case_keys(mock_client, monkeypatch):
    bot_config = {
        "bot_username": "@testbot",
        "settings": {"timeout": 15, "retry": 0},
        "commands": {
            "search": {
                "steps": [
                    {"action": "send_message", "content": "/search {query}"},
                    {
                        "action": "wait_response",
                        "expect": "text_message",
                        "extract": {"pattern": r"^(\d+)", "save_as": "choice"},
                    },
                ]
            }
        },
    }

    first_message = MagicMock()
    first_message.id = 101
    mock_client.send_message.return_value = first_message
    monkeypatch.setattr(
        "musigate.gateway.executor.Listener.wait",
        AsyncMock(return_value={"type": "text_message", "text": "1. First Song"}),
    )

    engine = Engine(bot_config, mock_client)
    context = await engine._run_async("search", query="First Song", return_context=True)

    assert "last_response" in context
    assert context["last_response"]["text"] == "1. First Song"
    assert context["last_action_message_id"] == 101
    assert context["extracted_data"]["choice"] == "1"
    assert "lastResponse" not in context
    assert "lastActionMessageId" not in context
    assert "extractedData" not in context


@pytest.mark.asyncio
async def test_engine_download_pick_uses_explicit_result_index(mock_client, monkeypatch, tmp_path):
    bot_config = {
        "bot_username": "@testbot",
        "settings": {"timeout": 15, "retry": 0},
        "commands": {
            "download": {
                "steps": [
                    {"action": "send_message", "content": "/search {query}"},
                    {"action": "wait_response", "expect": "inline_buttons"},
                    {"action": "click_button", "strategy": "match_text_index"},
                    {"action": "wait_response", "expect": "audio_file"},
                    {"action": "download", "output": "{title}.{ext}"},
                ]
            }
        },
    }

    first_message = MagicMock()
    first_message.id = 101
    mock_client.send_message.return_value = first_message

    mock_wait = AsyncMock(side_effect=[
        {
            "type": "inline_buttons",
            "text": "1. 海底 - 一支榴莲\n2. 海底（Live） - 凤凰传奇",
            "buttons": [
                [{"text": "1", "data": "1", "_message": first_message}],
                [{"text": "2", "data": "2", "_message": first_message}],
            ],
        },
        {
            "type": "audio_file",
            "title": "海底（Live）",
            "artist": "凤凰传奇",
            "ext": "mp3",
            "file": "mock_file_obj",
        },
    ])
    monkeypatch.setattr("musigate.gateway.executor.Listener.wait", mock_wait)

    engine = Engine(bot_config, mock_client)
    result = await engine._run_async(
        "download",
        query="海底",
        pick=2,
        output=str(tmp_path),
    )

    clicked_button = mock_client.click_button.await_args.args[0]
    assert clicked_button["text"] == "2"
    assert result.endswith("海底（Live）.mp3")
