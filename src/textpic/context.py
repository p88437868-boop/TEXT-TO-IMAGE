from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textpic.paths import app_data_dir
from textpic.services.analytics import AnalyticsService
from textpic.services.autostart import AutostartService
from textpic.services.clipboard import ClipboardService
from textpic.services.database import Database
from textpic.services.history_repo import HistoryRepository
from textpic.services.paste import PasteService
from textpic.services.renderer import RenderConfig, Renderer
from textpic.services.settings_service import SettingsService
from textpic.services.template_repo import TemplateRepository
from textpic.services.workflow import Workflow


@dataclass
class AppContext:
    database: Database
    settings: SettingsService
    history: HistoryRepository
    templates: TemplateRepository
    analytics: AnalyticsService
    renderer: Renderer
    clipboard: ClipboardService
    paste: PasteService
    workflow: Workflow
    autostart: AutostartService

    @property
    def data_dir(self) -> Path:
        return app_data_dir()

    def render_config(self) -> RenderConfig:
        return RenderConfig.from_dict(self.settings.render_defaults())

    def template_bindings(self) -> dict[str, str]:
        return {
            f"template:{record.id}": record.hotkey or ""
            for record in self.templates.list_all()
            if record.hotkey
        }

    def close(self) -> None:
        self.paste.set_delay(0)
        self.database.close()
