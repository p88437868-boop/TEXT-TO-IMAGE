from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QLineEdit, QWidget

from textpic.services.hotkeys import normalize_hotkey, parse_hotkey


class HotkeyBox(QLineEdit):
    changed = Signal(str)

    def __init__(
        self,
        sequence: str = "",
        allow_empty: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("HotkeyBox")
        self.setReadOnly(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setPlaceholderText("Click, then press a key")
        self.setToolTip("Click and press a key combination. Delete clears it.")
        self.allow_empty = allow_empty
        self.set_sequence(sequence, emit=False)

    def set_sequence(self, sequence: str, emit: bool = True) -> None:
        display = ""
        if sequence:
            try:
                display = normalize_hotkey(sequence)
            except ValueError:
                display = sequence
        self.setText(display)
        if emit:
            self.changed.emit(display)

    def sequence(self) -> str:
        return self.text().strip()

    def mousePressEvent(self, event) -> None:
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            if self.allow_empty or not self.text():
                self.clear()
                self.changed.emit("")
            event.accept()
            return
        if event.key() in (
            Qt.Key.Key_Control,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
            Qt.Key.Key_unknown,
        ):
            event.accept()
            return
        combination = event.keyCombination()
        sequence = QKeySequence(combination).toString(
            QKeySequence.SequenceFormat.PortableText
        )
        if not sequence:
            event.accept()
            return
        try:
            sequence = normalize_hotkey(sequence)
            parse_hotkey(sequence)
        except ValueError:
            self.style().unpolish(self)
            self.style().polish(self)
            event.accept()
            return
        self.setText(sequence)
        self.changed.emit(sequence)
        event.accept()

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        if not self.text():
            self.setText("")
