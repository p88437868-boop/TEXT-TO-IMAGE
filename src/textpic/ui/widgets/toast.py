from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from textpic.theme import tokens
from textpic.theme.icons import ICONS


TOAST_STYLES = {
    "success": ("SUCCESS", "check"),
    "error": ("DANGER", "alert"),
    "warning": ("WARNING", "alert"),
    "info": ("INFO", "bell"),
    "default": ("ACCENT", "check"),
}


class Toast(QFrame):
    def __init__(self, parent: QWidget, kind: str, message: str):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        color_token, icon_name = TOAST_STYLES.get(kind, TOAST_STYLES["default"])
        color = tokens.COLORS[color_token]
        self.setMinimumWidth(280)
        self.setMaximumWidth(420)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        bar = QFrame()
        bar.setFixedWidth(3)
        bar.setStyleSheet(f"background: {color}; border: none;")
        outer.addWidget(bar)
        content = QHBoxLayout()
        content.setContentsMargins(12, 11, 14, 11)
        content.setSpacing(9)
        icon = QLabel()
        icon.setPixmap(ICONS.pixmap(icon_name, color_token, 17))
        icon.setFixedSize(17, 17)
        text = QLabel(message)
        text.setObjectName("ToastText")
        text.setWordWrap(True)
        text.setMinimumWidth(220)
        text.setMaximumWidth(350)
        content.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        content.addWidget(text, 1)
        outer.addLayout(content)
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        self._fade = QPropertyAnimation(effect, b"opacity", self)
        self._fade.setDuration(160)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()

    def fade_out(self, on_done=None) -> None:
        effect = self.graphicsEffect()
        if effect is None:
            if on_done:
                on_done()
            return
        self._fade.stop()
        self._fade.setDuration(190)
        self._fade.setStartValue(effect.opacity())
        self._fade.setEndValue(0.0)
        if on_done:
            self._fade.finished.connect(on_done)
        self._fade.start()


class ToastManager(QObject):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent = parent
        self.current: Toast | None = None
        self._generation = 0
        parent.installEventFilter(self)

    def show(self, kind: str, message: str, duration: int = 2500) -> None:
        self._generation += 1
        generation = self._generation
        if self.current is not None:
            self.current.deleteLater()
            self.current = None
        toast = Toast(self.parent, kind, message)
        self.current = toast
        toast.adjustSize()
        self._place(toast)
        toast.show()
        toast.raise_()
        QTimer.singleShot(
            duration,
            lambda: self._dismiss(generation),
        )

    def success(self, message: str) -> None:
        self.show("success", message)

    def error(self, message: str) -> None:
        self.show("error", message)

    def warning(self, message: str) -> None:
        self.show("warning", message)

    def info(self, message: str) -> None:
        self.show("info", message)

    def _dismiss(self, generation: int) -> None:
        if generation != self._generation or self.current is None:
            return
        toast = self.current
        self.current = None
        toast.fade_out(toast.deleteLater)

    def _place(self, toast: Toast) -> None:
        margin = 22
        toast.move(
            max(margin, self.parent.width() - toast.width() - margin),
            max(margin, self.parent.height() - toast.height() - margin),
        )

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.Resize and self.current is not None:
            self._place(self.current)
        return super().eventFilter(watched, event)
