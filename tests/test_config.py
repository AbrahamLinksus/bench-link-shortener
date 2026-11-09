from pathlib import Path

import pytest

from link_shortener.config import DB_PATH_ENV, DEFAULT_DB_PATH, Settings


def test_settings_missing_env_uses_default() -> None:
    assert Settings.from_env({}).db_path == DEFAULT_DB_PATH


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_settings_blank_value_uses_default(raw: str) -> None:
    assert Settings.from_env({DB_PATH_ENV: raw}).db_path == DEFAULT_DB_PATH


def test_settings_env_override() -> None:
    assert Settings.from_env({DB_PATH_ENV: "x/y.db"}).db_path == Path("x/y.db")


def test_settings_value_is_stripped() -> None:
    assert Settings.from_env({DB_PATH_ENV: "  x/y.db "}).db_path == Path("x/y.db")


def test_settings_defaults_to_os_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DB_PATH_ENV, "from_os.db")
    assert Settings.from_env().db_path == Path("from_os.db")


def test_settings_is_immutable() -> None:
    settings = Settings(Path("a.db"))
    with pytest.raises(AttributeError):
        settings.db_path = Path("b.db")  # type: ignore[misc]
