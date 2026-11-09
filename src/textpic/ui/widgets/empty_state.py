from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from textpic.theme.icons import ICONS
from textpic.ui.widgets.controls import GhostButton


class EmptyState(QFrame):
    action_clicked = Signal()

    def __init__(
        self,
        icon_name: str = "image",
        title: str = "Nothing here yet",
        body: str = "",
        action_text: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("EmptyState")
        self.setMinimumHeight(190)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon = QLabel()
        self.icon.setPixmap(ICONS.pixmap(icon_name, "TEXT_MUTED", 30))
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title = QLabel(title)
        self.title.setObjectName("EmptyTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body = QLabel(body)
        self.body.setObjectName("EmptyBody")
        self.body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.setWordWrap(True)
        self.body.setMaximumWidth(360)
        self.action = GhostButton(action_text)
        self.action.setVisible(bool(action_text))
        self.action.clicked.connect(self.action_clicked.emit)
        layout.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)
        layout.addWidget(self.body)
        layout.addSpacing(2)
        layout.addWidget(self.action, 0, Qt.AlignmentFlag.AlignCenter)
