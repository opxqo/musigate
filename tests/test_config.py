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


def test_persist_env_values_writes_env_file(monkeypatch, tmp_path):
    monkeypatch.setenv("MUSIGATE_HOME", str(tmp_path / "musigate-home"))

    env_file = config_module.persist_env_values(
        {
            "TELEGRAM_API_ID": 123456,
            "TELEGRAM_API_HASH": "hash-value",
            "TELEGRAM_SESSION_NAME": "alpha-session",
        }
    )

    assert env_file == tmp_path / "musigate-home" / ".env"
    content = env_file.read_text(encoding="utf-8")
    assert "TELEGRAM_API_ID='123456'" in content
    assert "TELEGRAM_API_HASH='hash-value'" in content
    assert "TELEGRAM_SESSION_NAME='alpha-session'" in content


def test_resolve_session_name_uses_app_dir_for_bare_name(monkeypatch, tmp_path):
    monkeypatch.setenv("MUSIGATE_HOME", str(tmp_path / "musigate-home"))

    session_name = config_module.resolve_session_name("musigate")

    assert session_name == str(tmp_path / "musigate-home" / "musigate")


def test_resolve_session_name_preserves_explicit_path(tmp_path):
    explicit_path = tmp_path / "sessions" / "alpha"

    session_name = config_module.resolve_session_name(str(explicit_path))

    assert session_name == str(explicit_path)


def test_resolve_app_dir_defaults_to_hidden_dir_in_user_home(monkeypatch, tmp_path):
    monkeypatch.delenv("MUSIGATE_HOME", raising=False)
    monkeypatch.setattr(config_module.Path, "home", lambda: tmp_path)

    app_dir = config_module.resolve_app_dir()

    assert app_dir == tmp_path / ".musigate"
