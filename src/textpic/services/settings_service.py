from __future__ import annotations

import getpass
import json
from pathlib import Path
from typing import Any

from textpic.services.database import Database
from textpic.theme import tokens


DEFAULT_SETTINGS: dict[str, Any] = {
    "hotkey_render": "F6",
    "hotkey_render_alt": "Ctrl+F6",
    "hotkey_paste": "F9",
    "hotkey_paste_alt": "Ctrl+F9",
    "hotkey_combo": "F8",
    "hotkey_combo_alt": "Ctrl+F8",
    "workspace_name": "My Workspace",
    "display_name": getpass.getuser().title(),
    "role": "Sales & Support",
    "style_key": tokens.DEFAULT_RENDER["style_key"],
    "theme": tokens.DEFAULT_RENDER["theme"],
    "font": tokens.DEFAULT_RENDER["font"],
    "font_size": tokens.DEFAULT_RENDER["font_size"],
    "max_width": tokens.DEFAULT_RENDER["max_width"],
    "alignment": tokens.DEFAULT_RENDER["alignment"],
    "transparent": tokens.DEFAULT_RENDER["transparent"],
    "scale": tokens.DEFAULT_RENDER["scale"],
    "padding_x": tokens.DEFAULT_RENDER["padding_x"],
    "padding_y": tokens.DEFAULT_RENDER["padding_y"],
    "thumbnail_fit": tokens.DEFAULT_RENDER["thumbnail_fit"],
    "settings_version": 0,
    "start_with_windows": False,
    "start_minimized": False,
    "close_to_tray": True,
    "sound": False,
    "auto_clear": False,
    "retention_days": 90,
    "capture_mode": False,
    "paste_delay_ms": 80,
}

RETENTION_OPTIONS = [30, 90, 365, 0]

# Bump when a stored default has to be rewritten for an existing install.
SETTINGS_VERSION = 4


class SettingsService:
    def __init__(self, database: Database):
        self.database = database
        self._cache: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.reload()
        self._migrate()

    def _migrate(self) -> None:
        """Move saved renders off the old padded 2x canvas onto typed-message size."""
        try:
            stored = int(self.get("settings_version"))
        except (TypeError, ValueError):
            stored = 0
        if stored >= SETTINGS_VERSION:
            return
        try:
            if float(self.get("scale")) != 1.0:
                self.set("scale", 1.0)
        except (TypeError, ValueError):
            self.set("scale", 1.0)
        if str(self.get("thumbnail_fit")) in {"", "wide"}:
            self.set("thumbnail_fit", tokens.DEFAULT_RENDER["thumbnail_fit"])
        # Adopt the reference tool's metrics: Arial 22 px, 8/5 padding, 700 wrap.
        for key in ("font", "font_size", "max_width", "padding_x", "padding_y"):
            self.set(key, tokens.DEFAULT_RENDER[key])
        self.set("settings_version", SETTINGS_VERSION)

    def reload(self) -> None:
        values = dict(DEFAULT_SETTINGS)
        for row in self.database.query("SELECT key, value FROM settings"):
            if row["key"] not in DEFAULT_SETTINGS:
                continue
            try:
                values[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                values[row["key"]] = row["value"]
        self._cache = values

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._cache:
            return self._cache[key]
        return DEFAULT_SETTINGS.get(key, default)

    def get_bool(self, key: str) -> bool:
        return bool(self.get(key))

    def get_int(self, key: str) -> int:
        try:
            return int(self.get(key))
        except (TypeError, ValueError):
            return int(DEFAULT_SETTINGS.get(key, 0))

    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULT_SETTINGS:
            raise KeyError(f"Unknown setting: {key}")
        encoded = json.dumps(value, ensure_ascii=False)
        with self.database.connection:
            self.database.execute(
                """
                INSERT INTO settings(key, value) VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, encoded),
            )
        self._cache[key] = value

    def update(self, values: dict[str, Any]) -> None:
        filtered = {key: value for key, value in values.items() if key in DEFAULT_SETTINGS}
        if not filtered:
            return
        with self.database.connection:
            for key, value in filtered.items():
                self.database.execute(
                    """
                    INSERT INTO settings(key, value) VALUES(?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value
                    """,
                    (key, json.dumps(value, ensure_ascii=False)),
                )
        self._cache.update(filtered)

    def all(self) -> dict[str, Any]:
        return dict(self._cache)

    def render_defaults(self) -> dict[str, Any]:
        fit = str(self.get("thumbnail_fit") or "")
        if fit not in tokens.THUMBNAIL_RATIOS:
            fit = tokens.DEFAULT_RENDER["thumbnail_fit"]
        return {
            "style_key": self.get("style_key"),
            "theme": self.get("theme"),
            "font": self.get("font"),
            "font_size": self.get_int("font_size"),
            "max_width": self.get_int("max_width"),
            "alignment": self.get("alignment"),
            "transparent": self.get_bool("transparent"),
            "scale": float(self.get("scale")),
            "padding_x": self.get_int("padding_x"),
            "padding_y": self.get_int("padding_y"),
            "thumbnail_fit": fit,
        }

    def reset(self) -> None:
        with self.database.connection:
            self.database.execute("DELETE FROM settings")
        self._cache = dict(DEFAULT_SETTINGS)

    def export_json(self, path: Path) -> None:
        path = Path(path)
        path.write_text(
            json.dumps(self.all(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def import_json(self, path: Path) -> dict[str, Any]:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Settings file must contain a JSON object.")
        imported: dict[str, Any] = {}
        for key, value in raw.items():
            if key not in DEFAULT_SETTINGS:
                continue
            default = DEFAULT_SETTINGS[key]
            if isinstance(default, bool) and not isinstance(value, bool):
                continue
            if isinstance(default, int) and not isinstance(default, bool):
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    continue
            if isinstance(default, str) and not isinstance(value, str):
                continue
            imported[key] = value
        self.update(imported)
        return imported
