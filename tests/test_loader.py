import pytest
from musigate.adapters import loader as loader_module
from musigate.adapters.loader import list_bots, load_bot

def test_load_bot():
    config = load_bot("music163")
    assert config["name"] == "Music163"
    assert config["bot_username"] == "@Music163bot"
    assert "download" in config["commands"]

def test_load_music_v1_bot():
    config = load_bot("music_v1")
    assert config["name"] == "MusicV1"
    assert config["bot_username"] == "@music_v1bot"
    assert "search" in config["commands"]

def test_load_bot_missing_file():
    with pytest.raises(FileNotFoundError):
        load_bot("template")

def test_list_bots_excludes_template():
    configs = list_bots()
    names = {config["name"] for config in configs}
    assert "Music163" in names
    assert "MusicV1" in names
    assert "" not in names


def test_load_bot_falls_back_to_packaged_resource(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(loader_module, "PROJECT_ROOT", tmp_path / "missing_project_root")

    config = load_bot("music163")

    assert config["name"] == "Music163"
    assert config["bot_username"] == "@Music163bot"


def test_list_bots_falls_back_to_packaged_resources(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(loader_module, "PROJECT_ROOT", tmp_path / "missing_project_root")

    configs = list_bots()

    names = {config["name"] for config in configs}
    assert "Music163" in names
    assert "MusicV1" in names
