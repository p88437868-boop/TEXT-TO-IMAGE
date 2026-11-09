from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, Property
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QAbstractButton, QWidget

from textpic.theme import tokens


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._position = 0.0
        self._animation = QPropertyAnimation(self, b"position", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def sizeHint(self) -> QSize:
        return QSize(40, 23)

    def minimumSizeHint(self) -> QSize:
        return QSize(40, 23)

    def _get_position(self) -> float:
        return self._position

    def _set_position(self, value: float) -> None:
        self._position = value
        self.update()

    position = Property(float, _get_position, _set_position)

    def _animate(self, checked: bool) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._position)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self._position = 1.0 if checked else 0.0
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        width = 40.0
        height = 22.0
        top = (self.height() - height) / 2.0
        track = QRectF(0, top, width, height)
        if self.isChecked():
            color = tokens.qcolor(tokens.COLORS["ACCENT"])
        else:
            color = tokens.qcolor(tokens.COLORS["SURFACE_SELECTED"])
        painter.setPen(
            tokens.qcolor(
                tokens.COLORS["BORDER_STRONG"]
                if not self.isChecked()
                else tokens.COLORS["ACCENT"]
            )
        )
        painter.setBrush(color)
        painter.drawRoundedRect(track, height / 2.0, height / 2.0)
        handle_size = 16.0
        margin = 3.0
        travel = width - handle_size - margin * 2
        x = margin + travel * self._position
        handle = QRectF(x, top + margin, handle_size, handle_size)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(tokens.COLORS["TEXT_PRIMARY"]))
        painter.drawEllipse(handle)
        if self.hasFocus():
            painter.setPen(tokens.qcolor(tokens.COLORS["BORDER_FOCUS"]))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                QRectF(0.5, top + 0.5, width - 1, height - 1),
                height / 2.0,
                height / 2.0,
            )

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.toggle()
            event.accept()
            return
        super().keyPressEvent(event)
