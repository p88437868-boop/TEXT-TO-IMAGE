from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget


class Keycap(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("Keycap")
        self.setAlignment(self.alignment())
