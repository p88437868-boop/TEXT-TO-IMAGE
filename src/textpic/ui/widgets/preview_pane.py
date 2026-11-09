from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QWidget

from textpic.paths import assets_path
from textpic.theme import tokens
from textpic.theme.icons import ICONS


class PreviewPane(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(280, 220)
        self._image: QImage | None = None
        self._pixel_scale = 1.0
        self._placeholder_title = "Live preview"
        self._placeholder_body = "Start typing to see your chat bubble."
        self._checker = QPixmap(str(assets_path("checker.png")))

    def sizeHint(self) -> QSize:
        return QSize(520, 320)

    def set_image(self, image: QImage | None, pixel_scale: float = 1.0) -> None:
        self._image = image
        self._pixel_scale = max(0.25, float(pixel_scale))
        self.update()

    def set_placeholder(self, title: str, body: str) -> None:
        self._placeholder_title = title
        self._placeholder_body = body
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        clip = QPainterPath()
        clip.addRoundedRect(rect, 12, 12)
        painter.setClipPath(clip)
        painter.fillRect(rect, tokens.qcolor(tokens.COLORS["SURFACE_INPUT"]))
        self._draw_checker(painter, rect)
        if self._image is not None and not self._image.isNull():
            self._draw_image(painter, rect)
        else:
            self._draw_placeholder(painter, rect)
        painter.setClipping(False)
        painter.setPen(tokens.qcolor(tokens.COLORS["BORDER_SUBTLE"]))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 12, 12)

    def _draw_checker(self, painter: QPainter, rect: QRectF) -> None:
        if not self._checker.isNull():
            painter.drawTiledPixmap(rect.toRect(), self._checker)
            return
        tile = 16
        first = tokens.qcolor(tokens.COLORS["SURFACE_INPUT"])
        second = tokens.qcolor(tokens.COLORS["SURFACE_CARD"])
        x = 0
        row = 0
        while x < rect.width():
            y = 0
            column = row
            while y < rect.height():
                painter.fillRect(
                    QRectF(x, y, tile, tile),
                    second if (row + column) % 2 else first,
                )
                y += tile
                column += 1
            x += tile
            row += 1

    def _draw_image(self, painter: QPainter, rect: QRectF) -> None:
        available = rect.adjusted(28, 28, -28, -28)
        natural_width = self._image.width() / self._pixel_scale
        natural_height = self._image.height() / self._pixel_scale
        scale = min(
            1.0,
            available.width() / max(1.0, natural_width),
            available.height() / max(1.0, natural_height),
        )
        width = natural_width * scale
        height = natural_height * scale
        target = QRectF(
            rect.center().x() - width / 2,
            rect.center().y() - height / 2,
            width,
            height,
        )
        pixmap = QPixmap.fromImage(self._image)
        painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))

    def _draw_placeholder(self, painter: QPainter, rect: QRectF) -> None:
        icon = ICONS.pixmap("image", "TEXT_MUTED", 30)
        painter.drawPixmap(
            int(rect.center().x() - 15),
            int(rect.center().y() - 44),
            icon,
        )
        title_font = QFont("Inter")
        title_font.setFamilies(["Inter", "Segoe UI Variable", "Segoe UI"])
        title_font.setPixelSize(15)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(tokens.qcolor(tokens.COLORS["TEXT_SECONDARY"]))
        painter.drawText(
            QRectF(rect.left(), rect.center().y() - 4, rect.width(), 22),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            self._placeholder_title,
        )
        body_font = QFont("Inter")
        body_font.setFamilies(["Inter", "Segoe UI Variable", "Segoe UI"])
        body_font.setPixelSize(11)
        painter.setFont(body_font)
        painter.setPen(tokens.qcolor(tokens.COLORS["TEXT_MUTED"]))
        painter.drawText(
            QRectF(rect.left(), rect.center().y() + 18, rect.width(), 20),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            self._placeholder_body,
        )
