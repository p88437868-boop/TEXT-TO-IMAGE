from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication

from textpic.paths import images_dir
from textpic.services.clipboard import ClipboardService
from textpic.services.database import Database
from textpic.services.history_repo import HistoryRepository
from textpic.services.paste import PasteService
from textpic.services.renderer import RenderConfig, Renderer
from textpic.services.settings_service import SettingsService
from textpic.services.template_repo import TemplateRepository
from textpic.services.workflow import Workflow


def test_renderer_transparent_bubble(qapp) -> None:
    result = Renderer().render(
        "Hello 😊",
        RenderConfig(transparent=True, scale=1.5),
    )
    assert result.width > 20
    assert result.height > 20
    assert result.png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert result.image.pixelColor(0, 0).alpha() == 0
    assert result.image.hasAlphaChannel()


def test_renderer_rejects_empty_and_long_text(qapp) -> None:
    with pytest.raises(Exception):
        Renderer().render("   ", RenderConfig())
    with pytest.raises(Exception):
        Renderer().render("x" * 2001, RenderConfig())


def test_workflow_saves_png_and_sets_image_only_clipboard(
    tmp_path: Path, qapp, monkeypatch
) -> None:
    monkeypatch.setenv("TEXTPIC_DATA_DIR", str(tmp_path))
    database = Database(tmp_path / "textpic.db")
    settings = SettingsService(database)
    templates = TemplateRepository(database)
    history = HistoryRepository(database)
    workflow = Workflow(
        Renderer(),
        history,
        templates,
        settings,
        ClipboardService(),
        PasteService(0),
    )
    try:
        settings.update({"scale": 1.5})
        config = RenderConfig.from_dict(settings.render_defaults())
        record = workflow.render_text("Hello from the test 😊", config)
        path = Path(record.image_path or "")
        assert path.exists()
        assert path.is_relative_to(images_dir())
        assert path.stat().st_size > 100
        assert history.get(record.id) is not None

        mime = QGuiApplication.clipboard().mimeData()
        assert mime.hasImage()
        assert not any(fmt.startswith("text/") for fmt in mime.formats())
        assert QGuiApplication.clipboard().text() == ""
    finally:
        workflow.paste.set_delay(0)
        database.close()
