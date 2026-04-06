import json
from pathlib import Path

from typer.testing import CliRunner

from musigate import cli


runner = CliRunner()


def test_search_json_output(monkeypatch):
    async def fake_run_engine_command(command, bot, include_context=False, **kwargs):
        assert command == "search"
        assert bot == "music163"
        assert include_context is True
        assert kwargs["query"] == "Numb"
        assert kwargs["search_command"] == "/search"
        assert kwargs["source"] is None

        raw_text = "1. Numb - Linkin Park\n2. Numb 2024 - Demo Artist"
        return {
            "name": "Music163",
            "bot_username": "@Music163bot",
        }, {
            "result": raw_text,
            "last_response": {
                "type": "inline_buttons",
                "text": raw_text,
                "buttons": [
                    [{"text": "1", "data": "1"}],
                    [{"text": "2", "data": "2"}],
                ],
            },
        }

    monkeypatch.setattr(cli, "_run_engine_command", fake_run_engine_command)

    result = runner.invoke(cli.app, ["search", "Numb", "--bot", "music163", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "search"
    assert payload["query"] == "Numb"
    assert payload["results"][0]["index"] == 1
    assert payload["results"][0]["title"] == "Numb"
    assert payload["results"][0]["artist"] == "Linkin Park"


def test_download_json_output(monkeypatch):
    async def fake_run_engine_command(command, bot, include_context=False, **kwargs):
        assert command == "download"
        assert include_context is True
        assert kwargs["show_progress"] is False
        assert kwargs["pick"] == 2
        assert kwargs["search_command"] == "/search"
        assert kwargs["source"] is None

        return {
            "name": "Music163",
            "bot_username": "@Music163bot",
        }, {
            "pick": 2,
            "output": "./downloads",
            "result": "./downloads/Linkin Park-Numb.mp3",
            "result_filename": "Linkin Park-Numb.mp3",
            "last_response": {
                "type": "audio_file",
                "title": "Numb",
                "artist": "Linkin Park",
                "ext": "mp3",
                "duration": 185,
                "mime_type": "audio/mpeg",
                "size": 12345678,
                "file_name": "Linkin Park-Numb.mp3",
                "text": "Numb - Linkin Park",
            },
        }

    monkeypatch.setattr(cli, "_run_engine_command", fake_run_engine_command)
    monkeypatch.setattr(cli, "load_settings", lambda: {"download": {"defaultOutput": "./downloads"}})

    result = runner.invoke(cli.app, ["download", "Numb", "--bot", "music163", "--pick", "2", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["selected_index"] == 2
    assert payload["saved_path"].endswith("Linkin Park-Numb.mp3")
    assert payload["track"]["title"] == "Numb"
    assert payload["track"]["artist"] == "Linkin Park"
    assert payload["track"]["duration"] == 185
    assert payload["track"]["mime_type"] == "audio/mpeg"
    assert payload["track"]["size"] == 12345678
    assert payload["track"]["file_name"] == "Linkin Park-Numb.mp3"


def test_download_human_output_enables_progress(monkeypatch):
    async def fake_run_engine_command(command, bot, include_context=False, **kwargs):
        assert command == "download"
        assert include_context is False
        assert kwargs["show_progress"] is True
        assert kwargs["pick"] == 2
        assert kwargs["search_command"] == "/search"
        assert kwargs["source"] is None
        return {
            "name": "Music163",
            "bot_username": "@Music163bot",
        }, "./downloads/Linkin Park-Numb.mp3"

    monkeypatch.setattr(cli, "_run_engine_command", fake_run_engine_command)
    monkeypatch.setattr(cli, "load_settings", lambda: {"download": {"defaultOutput": "./downloads"}})

    result = runner.invoke(cli.app, ["download", "Numb", "--bot", "music163", "--pick", "2"])

    assert result.exit_code == 0
    assert "第 2 条结果" in result.stdout
    assert "Linkin Park-Numb.mp3" in result.stdout


def test_list_bots_json_output(monkeypatch):
    monkeypatch.setattr(
        cli,
        "list_bot_configs",
        lambda: [
            {
                "name": "Music163",
                "bot_username": "@Music163bot",
                "description": "Music downloader bot",
                "version": "1.0",
                "commands": {"download": {}, "search": {}},
            }
        ],
    )

    result = runner.invoke(cli.app, ["list-bots", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["count"] == 1
    assert payload["bots"][0]["commands"] == ["download", "search"]


def test_test_json_error_output(monkeypatch):
    def fake_load_bot(_bot):
        raise FileNotFoundError("missing bot config")

    monkeypatch.setattr(cli, "load_bot", fake_load_bot)

    result = runner.invoke(cli.app, ["test", "--bot", "missing", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "test"
    assert payload["bot"] == "missing"
    assert "missing bot config" in payload["error"]


def test_search_source_maps_music_v1_platform_command(monkeypatch):
    async def fake_run_engine_command(command, bot, include_context=False, **kwargs):
        assert command == "search"
        assert bot == "music_v1"
        assert include_context is True
        assert kwargs["query"] == "Sea Bottom"
        assert kwargs["source"] == "qq"
        assert kwargs["search_command"] == "/qq"

        raw_text = "1. Sea Bottom - Phoenix Legend"
        return {
            "name": "MusicV1",
            "bot_username": "@music_v1bot",
        }, {
            "source": "qq",
            "search_command": "/qq",
            "result": raw_text,
            "last_response": {
                "type": "inline_buttons",
                "text": raw_text,
                "buttons": [[{"text": "1", "data": "1"}]],
            },
        }

    monkeypatch.setattr(cli, "_run_engine_command", fake_run_engine_command)

    result = runner.invoke(
        cli.app,
        ["search", "Sea Bottom", "--bot", "music_v1", "--source", "qq", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["source"] == "qq"
    assert payload["results"][0]["index"] == 1


def test_download_source_rejects_unsupported_bot():
    result = runner.invoke(
        cli.app,
        ["download", "Numb", "--bot", "music163", "--source", "qq"],
    )

    assert result.exit_code == 1
    assert '--source is not supported for bot "music163"' in result.stdout


def test_login_prompts_for_missing_credentials_and_saves(monkeypatch, tmp_path):
    captured = {}

    class FakeAuth:
        def __init__(self, api_id, api_hash, session_name="musigate", proxy=None):
            captured["api_id"] = api_id
            captured["api_hash"] = api_hash
            captured["session_name"] = session_name
            captured["proxy"] = proxy

        async def login(self):
            captured["login_called"] = True
            return True

    monkeypatch.setattr(
        cli,
        "load_settings",
        lambda: {
            "telegram": {
                "apiId": "",
                "apiHash": "",
                "sessionName": "musigate",
                "proxy": {"enabled": False},
            }
        },
    )
    monkeypatch.setattr(cli, "TelegramAuth", FakeAuth)

    env_path = tmp_path / ".env"

    def fake_persist_env_values(values):
        captured["saved_values"] = values
        return env_path

    monkeypatch.setattr(cli, "persist_env_values", fake_persist_env_values)
    monkeypatch.setattr(cli, "resolve_env_file", lambda: env_path)
    monkeypatch.setattr(cli, "resolve_session_name", lambda name: str(tmp_path / "sessions" / name))

    result = runner.invoke(cli.app, ["login"], input="123456\nsecret-hash\n")

    assert result.exit_code == 0
    assert captured["api_id"] == 123456
    assert captured["api_hash"] == "secret-hash"
    assert captured["session_name"] == str(tmp_path / "sessions" / "musigate")
    assert captured["login_called"] is True
    assert captured["saved_values"] == {
        "TELEGRAM_API_ID": 123456,
        "TELEGRAM_API_HASH": "secret-hash",
        "TELEGRAM_SESSION_NAME": "musigate",
    }
    assert str(Path(env_path)) in result.stdout.replace("\n", "")
