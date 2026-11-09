from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from textpic.theme.icons import ICONS
from textpic.ui.widgets.keycap import Keycap


class PrimaryButton(QPushButton):
    def __init__(
        self,
        text: str = "",
        icon_name: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent)
        self.setProperty("role", "primary")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_name:
            self.setIcon(ICONS.icon(icon_name, "TEXT_ON_ACCENT", 18))


class GhostButton(QPushButton):
    def __init__(
        self,
        text: str = "",
        icon_name: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent)
        self.setProperty("role", "ghost")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_name:
            self.setIcon(ICONS.icon(icon_name, "TEXT_SECONDARY", 18))


class DangerButton(QPushButton):
    def __init__(
        self,
        text: str = "",
        icon_name: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent)
        self.setProperty("role", "danger")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_name:
            self.setIcon(ICONS.icon(icon_name, "DANGER", 18))


class LinkButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setProperty("role", "link")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class IconButton(QPushButton):
    def __init__(
        self,
        icon_name: str,
        tooltip: str = "",
        color: str = "TEXT_MUTED",
        size: int = 18,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setProperty("role", "icon")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(size, size))
        self.setIcon(ICONS.icon(icon_name, color, size))
        self.setToolTip(tooltip)
        self.setFixedSize(34, 34)


class Chip(QLabel):
    def __init__(
        self,
        text: str = "",
        tone: str = "accent",
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent)
        self.setObjectName("Chip")
        self.setProperty("tone", tone)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def set_tone(self, tone: str) -> None:
        self.setProperty("tone", tone)
        self.style().unpolish(self)
        self.style().polish(self)


class KeycapButton(QWidget):
    def __init__(
        self,
        button: QPushButton,
        key: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(button)
        self.keycap = Keycap(key)
        layout.addWidget(self.keycap)

    def set_key(self, key: str) -> None:
        self.keycap.setText(key)


def divider(horizontal: bool = True) -> QFrame:
    frame = QFrame()
    frame.setObjectName("VLine" if not horizontal else "Divider")
    if horizontal:
        frame.setFixedHeight(1)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    else:
        frame.setFixedWidth(1)
        frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
    return frame


def icon_label(
    icon_name: str,
    color: str = "ACCENT",
    size: int = 20,
    parent: QWidget | None = None,
) -> QLabel:
    label = QLabel(parent)
    label.setPixmap(ICONS.pixmap(icon_name, color, size))
    label.setFixedSize(size, size)
    return label
