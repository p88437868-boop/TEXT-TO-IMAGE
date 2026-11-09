from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from textpic.paths import assets_path


class TrayService(QObject):
    show_requested = Signal()
    render_requested = Signal()
    paste_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.available = QSystemTrayIcon.isSystemTrayAvailable()
        self.tray: QSystemTrayIcon | None = None
        self._render_action: QAction | None = None
        self._paste_action: QAction | None = None
        if not self.available:
            return

        icon_path = assets_path("tray.ico")
        if not icon_path.exists():
            icon_path = assets_path("app.ico")
        self.tray = QSystemTrayIcon(QIcon(str(icon_path)), self)
        self.tray.setToolTip("TextPic Studio — F6 to render, F9 to paste")

        menu = QMenu()
        show_action = QAction("Show TextPic Studio", menu)
        show_action.triggered.connect(self.show_requested.emit)
        self._render_action = QAction("Render current message (F6)", menu)
        self._render_action.triggered.connect(self.render_requested.emit)
        self._paste_action = QAction("Paste image (F9)", menu)
        self._paste_action.triggered.connect(self.paste_requested.emit)
        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(self._render_action)
        menu.addAction(self._paste_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.show_requested.emit()

    def set_hotkeys(self, render: str, paste: str) -> None:
        render = render or "F6"
        paste = paste or "F9"
        if self.tray is not None:
            self.tray.setToolTip(
                f"TextPic Studio — {render} to render, {paste} to paste"
            )
        if self._render_action is not None:
            self._render_action.setText(f"Render current message ({render})")
        if self._paste_action is not None:
            self._paste_action.setText(f"Paste image ({paste})")

    def show_message(self, title: str, message: str) -> None:
        if self.tray is not None:
            self.tray.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )

    def hide(self) -> None:
        if self.tray is not None:
            self.tray.hide()
