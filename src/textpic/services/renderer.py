from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRect, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QPainter,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextOption,
)

from textpic.theme import tokens


MAX_TEXT_LENGTH = 2000
LINE_HEIGHT_FACTOR = 1.3
BUBBLE_RADIUS = 18

# The reference renderer draws at 3x and averages back down to 1x, which is
# what makes its text look sharp at the message's own pixel size. Downscaling
# never changes the final dimensions: the output stays scale * logical size.
SUPERSAMPLE = 3


class RenderError(Exception):
    """A user-facing rendering problem."""


class EmptyTextError(RenderError):
    pass


class TextTooLongError(RenderError):
    pass


@dataclass(frozen=True)
class RenderConfig:
    style_key: str = tokens.DEFAULT_RENDER["style_key"]
    theme: str = tokens.DEFAULT_RENDER["theme"]
    font: str = tokens.DEFAULT_RENDER["font"]
    font_size: int = tokens.DEFAULT_RENDER["font_size"]
    max_width: int = tokens.DEFAULT_RENDER["max_width"]
    alignment: str = tokens.DEFAULT_RENDER["alignment"]
    transparent: bool = tokens.DEFAULT_RENDER["transparent"]
    scale: float = tokens.DEFAULT_RENDER["scale"]
    padding_x: int = tokens.DEFAULT_RENDER["padding_x"]
    padding_y: int = tokens.DEFAULT_RENDER["padding_y"]
    thumbnail_fit: str = tokens.DEFAULT_RENDER["thumbnail_fit"]

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "RenderConfig":
        fit = str(
            values.get("thumbnail_fit", tokens.DEFAULT_RENDER["thumbnail_fit"])
        ).lower()
        if fit not in tokens.THUMBNAIL_RATIOS:
            fit = tokens.DEFAULT_RENDER["thumbnail_fit"]
        return cls(
            style_key=str(values.get("style_key", tokens.DEFAULT_RENDER["style_key"])),
            theme=str(values.get("theme", tokens.DEFAULT_RENDER["theme"])),
            font=str(values.get("font", tokens.DEFAULT_RENDER["font"])),
            font_size=int(values.get("font_size", tokens.DEFAULT_RENDER["font_size"])),
            max_width=int(values.get("max_width", tokens.DEFAULT_RENDER["max_width"])),
            alignment=str(
                values.get("alignment", tokens.DEFAULT_RENDER["alignment"])
            ).lower(),
            transparent=bool(
                values.get("transparent", tokens.DEFAULT_RENDER["transparent"])
            ),
            scale=float(values.get("scale", tokens.DEFAULT_RENDER["scale"])),
            padding_x=int(
                values.get("padding_x", tokens.DEFAULT_RENDER["padding_x"])
            ),
            padding_y=int(
                values.get("padding_y", tokens.DEFAULT_RENDER["padding_y"])
            ),
            thumbnail_fit=fit,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "style_key": self.style_key,
            "theme": self.theme,
            "font": self.font,
            "font_size": self.font_size,
            "max_width": self.max_width,
            "alignment": self.alignment,
            "transparent": self.transparent,
            "scale": self.scale,
            "padding_x": self.padding_x,
            "padding_y": self.padding_y,
            "thumbnail_fit": self.thumbnail_fit,
        }


@dataclass(frozen=True)
class RenderResult:
    image: QImage
    png_bytes: bytes
    width: int
    height: int
    line_count: int


class Renderer:
    def render(self, text: str, config: RenderConfig) -> RenderResult:
        self._validate(text, config)
        preset = tokens.BUBBLE_PRESETS.get(config.style_key)
        if preset is None:
            raise RenderError(f"Unknown style preset: {config.style_key}")

        font_size = max(10, min(48, config.font_size))
        scale = max(1.0, min(4.0, float(config.scale)))
        line_height = font_size * LINE_HEIGHT_FACTOR
        pad_x = 0 if preset.plain else max(0, config.padding_x)
        pad_y = 0 if preset.plain else max(0, config.padding_y)
        max_text_width = max(40, config.max_width - (pad_x * 2))

        font = QFont(config.font)
        font.setPixelSize(font_size)
        font.setWeight(QFont.Weight.Normal)
        # Same preference order as the reference's load_font(), plus the emoji
        # fonts so emoji keep rendering as colour glyphs instead of boxes.
        font.setFamilies(
            [
                config.font,
                "Segoe UI Emoji",
                "Segoe UI Symbol",
                *tokens.RENDER_FONT_FALLBACKS,
            ]
        )

        document = QTextDocument()
        document.setDocumentMargin(0)
        document.setDefaultFont(font)
        document.setPlainText(text)
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        option.setAlignment(
            Qt.AlignmentFlag.AlignRight
            if config.alignment == "right"
            else Qt.AlignmentFlag.AlignLeft
        )
        document.setDefaultTextOption(option)

        cursor = QTextCursor(document)
        cursor.select(QTextCursor.SelectionType.Document)
        char_format = QTextCharFormat()
        char_format.setFont(font)
        char_format.setForeground(QColor(preset.text))
        cursor.mergeCharFormat(char_format)

        block_format = QTextBlockFormat()
        block_format.setLineHeight(
            line_height, QTextBlockFormat.LineHeightTypes.FixedHeight.value
        )
        block_format.setAlignment(
            Qt.AlignmentFlag.AlignRight
            if config.alignment == "right"
            else Qt.AlignmentFlag.AlignLeft
        )
        for index in range(document.blockCount()):
            block = document.findBlockByNumber(index)
            block_cursor = QTextCursor(block)
            block_cursor.setBlockFormat(block_format)

        document.setTextWidth(max_text_width)
        natural_width = document.idealWidth()
        text_width = max(1, min(max_text_width, int(math.ceil(natural_width))))
        document.setTextWidth(text_width)
        natural_width = document.idealWidth()
        adjusted = max(1, min(max_text_width, int(math.ceil(natural_width))))
        if adjusted != text_width:
            text_width = adjusted
            document.setTextWidth(text_width)
        text_height = max(1, int(math.ceil(document.size().height())))

        content_width = text_width + pad_x * 2
        content_height = text_height + pad_y * 2
        pixel_width = max(1, int(math.ceil(content_width * scale)))
        pixel_height = max(1, int(math.ceil(content_height * scale)))
        render_scale = scale * SUPERSAMPLE
        hi_width = max(1, int(math.ceil(content_width * render_scale)))
        hi_height = max(1, int(math.ceil(content_height * render_scale)))

        image = QImage(
            hi_width,
            hi_height,
            QImage.Format.Format_ARGB32_Premultiplied,
        )
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.scale(render_scale, render_scale)
            if not config.transparent:
                painter.fillRect(
                    QRectF(0, 0, content_width, content_height),
                    tokens.qcolor(tokens.render_theme_background(config.theme)),
                )
            if not preset.plain:
                radius = min(
                    BUBBLE_RADIUS,
                    content_width / 2.0,
                    content_height / 2.0,
                )
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(tokens.qcolor(preset.fill))
                painter.drawRoundedRect(
                    QRectF(0, 0, content_width, content_height),
                    radius,
                    radius,
                )
            painter.translate(pad_x, pad_y)
            painter.setClipRect(QRectF(0, 0, text_width, text_height))
            document.drawContents(
                painter,
                QRectF(0, 0, text_width, text_height),
            )
        finally:
            painter.end()

        if image.width() != pixel_width or image.height() != pixel_height:
            image = image.scaled(
                pixel_width,
                pixel_height,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        if preset.plain and config.transparent:
            image = self._trim_transparent(image)
        ratio = tokens.THUMBNAIL_RATIOS.get(config.thumbnail_fit, 0.0)
        if ratio > 0:
            background = (
                None
                if config.transparent
                else tokens.qcolor(tokens.render_theme_background(config.theme))
            )
            image = self._fit_thumbnail(image, ratio, background)
        png_bytes = self._to_png(image)
        return RenderResult(
            image=image,
            png_bytes=png_bytes,
            width=image.width(),
            height=image.height(),
            line_count=max(1, round(text_height / max(1.0, line_height))),
        )

    @staticmethod
    def _validate(text: str, config: RenderConfig) -> None:
        if not text or not text.strip():
            raise EmptyTextError("Type a message first.")
        if len(text) > MAX_TEXT_LENGTH:
            raise TextTooLongError(
                f"Messages are limited to {MAX_TEXT_LENGTH:,} characters."
            )
        if config.style_key not in tokens.BUBBLE_PRESETS:
            raise RenderError("Choose a valid style preset.")
        if config.alignment not in {"left", "right"}:
            raise RenderError("Alignment must be left or right.")
        if int(config.max_width) < 80:
            raise RenderError("Maximum bubble width is too small.")
        if float(config.scale) <= 0:
            raise RenderError("Scale must be greater than zero.")

    @staticmethod
    def _trim_transparent(image: QImage) -> QImage:
        width = image.width()
        height = image.height()
        left, top, right, bottom = width, height, -1, -1
        for y in range(height):
            for x in range(width):
                if (image.pixel(x, y) >> 24) & 0xFF:
                    if x < left:
                        left = x
                    if x > right:
                        right = x
                    if y < top:
                        top = y
                    if y > bottom:
                        bottom = y
        if right < left or bottom < top:
            return image
        rect = QRect(left, top, right - left + 1, bottom - top + 1)
        if rect == image.rect():
            return image
        return image.copy(rect)

    @staticmethod
    def _fit_thumbnail(
        image: QImage, ratio: float, background: QColor | None
    ) -> QImage:
        """Adds just enough vertical padding to reach a thumbnail ratio.

        Social previews crop images wider than their card, which cuts the
        sides off short messages. Padding the height to the card's aspect
        ratio keeps the bubble inside the crop, and images that are already
        at or below the ratio are returned untouched.
        """
        width = image.width()
        height = image.height()
        target_height = max(height, int(round(width / ratio)))
        if target_height <= height:
            return image
        canvas = QImage(
            width, target_height, QImage.Format.Format_ARGB32_Premultiplied
        )
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        try:
            if background is not None:
                painter.fillRect(canvas.rect(), background)
            painter.drawImage(0, (target_height - height) // 2, image)
        finally:
            painter.end()
        return canvas

    @staticmethod
    def _to_png(image: QImage) -> bytes:
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        try:
            image.save(buffer, "PNG")
            data = bytes(buffer.data())
        finally:
            buffer.close()
        return data
