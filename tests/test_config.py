from musigate.utils import config as config_module


def test_load_settings_falls_back_to_packaged_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "PROJECT_ROOT", tmp_path / "missing_project_root")
    monkeypatch.delenv("MUSIGATE_SETTINGS_FILE", raising=False)

    settings = config_module.load_settings()

    assert settings["download"]["defaultOutput"] == "./downloads"
    assert settings["telegram"]["sessionName"] == "musigate"


def test_load_settings_prefers_custom_settings_file(monkeypatch, tmp_path):
    custom_dir = tmp_path / "custom"
    custom_dir.mkdir()
    settings_file = custom_dir / "settings.yaml"
    settings_file.write_text(
        "download:\n  defaultOutput: ./alpha-downloads\ntelegram:\n  sessionName: alpha\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MUSIGATE_SETTINGS_FILE", str(settings_file))
    monkeypatch.setenv("TELEGRAM_SESSION_NAME", "")

    settings = config_module.load_settings()

    assert settings["download"]["defaultOutput"] == "./alpha-downloads"
    assert settings["telegram"]["sessionName"] == "alpha"
