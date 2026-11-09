from __future__ import annotations

from pathlib import Path

import pytest

from textpic.services.database import Database
from textpic.services.renderer import RenderConfig
from textpic.services.settings_service import DEFAULT_SETTINGS, SettingsService


def make_settings(tmp_path: Path) -> tuple[Database, SettingsService]:
    database = Database(tmp_path / "settings.db")
    return database, SettingsService(database)


def test_scale_roundtrip_preserves_fraction(tmp_path: Path) -> None:
    database, settings = make_settings(tmp_path)
    try:
        settings.update({"scale": 1.5})
        defaults = settings.render_defaults()
        assert defaults["scale"] == 1.5
        assert RenderConfig.from_dict(defaults).scale == 1.5
    finally:
        database.close()


def test_unknown_and_invalid_settings_are_ignored(tmp_path: Path) -> None:
    database, settings = make_settings(tmp_path)
    try:
        settings.update({"not_a_setting": 1, "font_size": 21})
        assert "not_a_setting" not in settings.all()
        assert settings.get_int("font_size") == 21
        with pytest.raises(KeyError):
            settings.set("not_a_setting", 1)
    finally:
        database.close()


def test_export_import_roundtrip(tmp_path: Path) -> None:
    database, settings = make_settings(tmp_path)
    try:
        settings.update(
            {
                "display_name": "Maya",
                "workspace_name": "Support",
                "transparent": False,
                "retention_days": 30,
            }
        )
        path = tmp_path / "settings.json"
        settings.export_json(path)
        settings.reset()
        assert settings.get("display_name") == DEFAULT_SETTINGS["display_name"]
        imported = settings.import_json(path)
        assert imported["display_name"] == "Maya"
        assert settings.get("workspace_name") == "Support"
        assert settings.get_bool("transparent") is False
        assert settings.get_int("retention_days") == 30
    finally:
        database.close()
