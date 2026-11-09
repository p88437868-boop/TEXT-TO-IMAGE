from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return project_root()


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def assets_path(*parts: str) -> Path:
    return resource_path("assets", *parts)


def app_data_dir() -> Path:
    override = os.environ.get("TEXTPIC_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "TextPicStudio"
    return Path.home() / "AppData" / "Roaming" / "TextPicStudio"


def ensure_data_dirs() -> Path:
    root = app_data_dir()
    (root / "images").mkdir(parents=True, exist_ok=True)
    return root


def database_path() -> Path:
    return app_data_dir() / "textpic.db"


def images_dir() -> Path:
    return app_data_dir() / "images"


def new_image_path() -> Path:
    from datetime import datetime
    from uuid import uuid4

    now = datetime.now()
    folder = images_dir() / f"{now:%Y}" / f"{now:%m}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{uuid4()}.png"


def log_path() -> Path:
    ensure_data_dirs()
    return app_data_dir() / "textpic.log"
