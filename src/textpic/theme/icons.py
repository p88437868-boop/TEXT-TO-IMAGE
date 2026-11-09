from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from textpic.theme import tokens


class IconFactory:
    def __init__(self, icons_dir: Path):
        self.icons_dir = Path(icons_dir)
        self._cache: dict[tuple[str, str, int, float], QPixmap] = {}

    def pixmap(
        self,
        name: str,
        color: str = "TEXT_SECONDARY",
        size: int = 24,
        dpr: float = 1.0,
    ) -> QPixmap:
        key = (name, color, size, dpr)
        if key in self._cache:
            return self._cache[key]
        path = self.icons_dir / f"{name}.svg"
        resolved = tokens.token(color) if color in tokens.COLORS else color
        if not path.exists():
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
        else:
            svg = path.read_text(encoding="utf-8").replace("currentColor", resolved)
            renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
            pixmap = QPixmap(max(1, round(size * dpr)), max(1, round(size * dpr)))
            pixmap.setDevicePixelRatio(dpr)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            renderer.render(painter)
            painter.end()
        self._cache[key] = pixmap
        return pixmap

    def icon(
        self,
        name: str,
        color: str = "TEXT_SECONDARY",
        size: int = 24,
    ) -> QIcon:
        icon = QIcon()
        icon.addPixmap(self.pixmap(name, color, size, 1.0))
        icon.addPixmap(self.pixmap(name, color, size, 2.0))
        return icon

from textpic.paths import assets_path as _assets_path

ICONS = IconFactory(_assets_path("icons"))
