from __future__ import annotations

from PySide6.QtCore import QByteArray, QMimeData
from PySide6.QtGui import QImage, QGuiApplication


class ClipboardService:
    """Publishes an image with image formats only (never text formats)."""

    def set_image(self, image: QImage, png_bytes: bytes | None = None) -> None:
        mime = QMimeData()
        mime.setImageData(image)
        if png_bytes:
            mime.setData("image/png", QByteArray(png_bytes))
        QGuiApplication.clipboard().setMimeData(mime)

    def text(self) -> str:
        return QGuiApplication.clipboard().text()

    def clear(self) -> None:
        QGuiApplication.clipboard().clear()
