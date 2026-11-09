from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
import tempfile
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import Qt, qVersion
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QGuiApplication,
    QIcon,
    QPalette,
)
from PySide6.QtWidgets import QApplication, QMessageBox

from textpic.__version__ import APP_NAME, VERSION
from textpic.context import AppContext
from textpic.native import win32
from textpic.paths import (
    app_data_dir,
    assets_path,
    database_path,
    ensure_data_dirs,
    log_path,
    new_image_path,
)
from textpic.services.analytics import AnalyticsService
from textpic.services.autostart import AutostartService
from textpic.services.clipboard import ClipboardService
from textpic.services.database import Database
from textpic.services.history_repo import HistoryRepository
from textpic.services.hotkeys import normalize_hotkey, parse_hotkey
from textpic.services.paste import PasteService
from textpic.services.renderer import RenderConfig, Renderer
from textpic.services.settings_service import SettingsService
from textpic.services.single_instance import SingleInstance
from textpic.services.template_repo import TemplateRepository
from textpic.services.workflow import Workflow
from textpic.theme import tokens
from textpic.theme.qss import build_stylesheet
from textpic.ui.shell import MainWindow


LOGGER = logging.getLogger("textpic")
APP_ID = "TextPicStudio.Desktop.1"


def configure_logging() -> None:
    ensure_data_dirs()
    LOGGER.setLevel(logging.INFO)
    if LOGGER.handlers:
        return
    handler = RotatingFileHandler(
        log_path(),
        maxBytes=1_500_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    LOGGER.addHandler(handler)


def build_context(database_file: Path | None = None) -> AppContext:
    database = Database(database_file or database_path())
    settings = SettingsService(database)
    templates = TemplateRepository(database)
    templates.seed_defaults()
    history = HistoryRepository(database)
    analytics = AnalyticsService(database)
    renderer = Renderer()
    clipboard = ClipboardService()
    paste = PasteService(settings.get_int("paste_delay_ms"))
    workflow = Workflow(
        renderer,
        history,
        templates,
        settings,
        clipboard,
        paste,
    )
    return AppContext(
        database=database,
        settings=settings,
        history=history,
        templates=templates,
        analytics=analytics,
        renderer=renderer,
        clipboard=clipboard,
        paste=paste,
        workflow=workflow,
        autostart=AutostartService(),
    )


def load_fonts() -> None:
    folder = assets_path("fonts")
    if not folder.exists():
        return
    for path in sorted(folder.glob("*")):
        if path.suffix.lower() in {".ttf", ".otf"}:
            QFontDatabase.addApplicationFont(str(path))


def apply_palette(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(tokens.COLORS["BG_CANVAS"]))
    palette.setColor(
        QPalette.ColorRole.WindowText, QColor(tokens.COLORS["TEXT_PRIMARY"])
    )
    palette.setColor(QPalette.ColorRole.Base, QColor(tokens.COLORS["SURFACE_INPUT"]))
    palette.setColor(
        QPalette.ColorRole.AlternateBase, QColor(tokens.COLORS["SURFACE_CARD"])
    )
    palette.setColor(QPalette.ColorRole.Text, QColor(tokens.COLORS["TEXT_PRIMARY"]))
    palette.setColor(
        QPalette.ColorRole.Button, QColor(tokens.COLORS["SURFACE_CARD"])
    )
    palette.setColor(
        QPalette.ColorRole.ButtonText, QColor(tokens.COLORS["TEXT_PRIMARY"])
    )
    palette.setColor(QPalette.ColorRole.Highlight, QColor(tokens.COLORS["ACCENT"]))
    palette.setColor(
        QPalette.ColorRole.HighlightedText, QColor(tokens.COLORS["TEXT_ON_ACCENT"])
    )
    palette.setColor(
        QPalette.ColorRole.PlaceholderText, QColor(tokens.COLORS["TEXT_MUTED"])
    )
    palette.setColor(
        QPalette.ColorRole.ToolTipBase, QColor(tokens.COLORS["SURFACE_SELECTED"])
    )
    palette.setColor(
        QPalette.ColorRole.ToolTipText, QColor(tokens.COLORS["TEXT_PRIMARY"])
    )
    app.setPalette(palette)


def create_application() -> QApplication:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication([sys.argv[0]])
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("TextPic Studio")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    load_fonts()
    font = QFont("Inter")
    font.setFamilies(["Inter", "Segoe UI Variable", "Segoe UI"])
    font.setPixelSize(13)
    app.setFont(font)
    apply_palette(app)
    app.setStyleSheet(build_stylesheet(assets_path()))
    icon_path = assets_path("app.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    win32.set_app_user_model_id(APP_ID)
    return app


def install_exception_hook(app: QApplication) -> None:
    def hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        LOGGER.error("Unhandled exception:\n%s", text)
        if app.instance() is not None:
            QMessageBox.critical(
                None,
                "TextPic Studio",
                "An unexpected error occurred. Details were written to the log file.",
            )

    sys.excepthook = hook


def selftest(app: QApplication, temp_dir: Path) -> str:
    checks: list[str] = []
    context = build_context(temp_dir / "textpic.db")
    renderer = context.renderer
    config = RenderConfig.from_dict(context.settings.render_defaults())
    result = renderer.render("Selftest 😊 — nice to meet you!", config)
    if result.image.isNull() or result.width < 20 or result.height < 20:
        raise RuntimeError("Renderer returned an invalid image")
    if not result.png_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Renderer returned invalid PNG bytes")
    checks.append(f"render {result.width}x{result.height}")

    path = new_image_path()
    if not result.image.save(str(path), "PNG"):
        raise RuntimeError("Could not save rendered image")
    record = context.history.add(
        text="Selftest 😊 — nice to meet you!",
        style_key=config.style_key,
        theme=config.theme,
        font=config.font,
        font_size=config.font_size,
        scale=config.scale,
        image_path=str(path),
    )
    if context.history.get(record.id) is None:
        raise RuntimeError("History did not return the saved record")
    checks.append("history")

    for sequence in ("F6", "F9", "Ctrl+Alt+1", "Ctrl+Shift+F12"):
        parse_hotkey(sequence)
        normalize_hotkey(sequence)
    checks.append("hotkeys")

    families = set(QFontDatabase.families())
    if "Segoe UI" not in families:
        raise RuntimeError("Windows UI fonts are unavailable")
    checks.append(f"fonts {len(families)}")

    window = MainWindow(context)
    if len(window.pages) != 7:
        raise RuntimeError("Not all pages were created")
    for key in window.pages:
        window.show_page(key)
        app.processEvents()
    checks.append("pages")
    window.shutdown()
    context.close()
    checks.append("cleanup")
    message = "SELFTEST OK: " + ", ".join(checks)
    LOGGER.info(message)
    return message


def run_selftest() -> int:
    temp_dir = Path(tempfile.mkdtemp(prefix="textpic-selftest-"))
    report = Path(tempfile.gettempdir()) / "TextPicStudio-selftest.txt"
    os.environ["TEXTPIC_DATA_DIR"] = str(temp_dir)
    configure_logging()
    try:
        app = create_application()
        message = selftest(app, temp_dir)
        report.write_text(
            f"{message}\nVersion: {VERSION}\nQt: {qVersion()}\n",
            encoding="utf-8",
        )
        return 0
    except Exception:
        detail = traceback.format_exc()
        LOGGER.exception("Selftest failed")
        report.write_text("SELFTEST FAILED\n" + detail, encoding="utf-8")
        return 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run() -> int:
    args = [
        arg
        for arg in sys.argv[1:]
        if arg
        in {
            "--startup",
            "--selftest",
            "--enable-autostart",
            "--disable-autostart",
            "--version",
        }
    ]
    if "--version" in args:
        print(f"{APP_NAME} {VERSION}")
        return 0
    if "--enable-autostart" in args or "--disable-autostart" in args:
        service = AutostartService()
        try:
            service.set_enabled("--enable-autostart" in args)
        except OSError:
            return 1
        return 0
    if "--selftest" in args:
        return run_selftest()

    configure_logging()
    LOGGER.info("Starting %s %s", APP_NAME, VERSION)
    app = create_application()
    install_exception_hook(app)
    single = SingleInstance()
    if not single.acquire():
        return 0
    context: AppContext | None = None
    window: MainWindow | None = None
    try:
        context = build_context()
        context.workflow.apply_retention()
        window = MainWindow(context)
        single.activate_requested.connect(window.show_window)
        window.show_startup()
        return app.exec()
    except Exception:
        LOGGER.exception("Fatal startup error")
        QMessageBox.critical(
            None,
            APP_NAME,
            "TextPic Studio could not start. Check the log in your TextPicStudio data folder.",
        )
        return 1
    finally:
        if window is not None:
            window.shutdown()
        if context is not None:
            try:
                context.close()
            except Exception:
                LOGGER.exception("Could not close the database cleanly")
        single.close()


if __name__ == "__main__":
    raise SystemExit(run())
