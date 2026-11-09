from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtGui import QColor


COLORS: dict[str, str] = {
    "BG_CANVAS": "#0B0B10",
    "BG_GLOW_START": "#0A1830",
    "BG_GLOW_END": "#2A0F4D",
    "SURFACE_SIDEBAR": "#17171B",
    "SURFACE_CARD": "#1E1E23",
    "SURFACE_CARD_HOVER": "#26262C",
    "SURFACE_INPUT": "#141418",
    "SURFACE_SELECTED": "#2B2B31",
    "SURFACE_OVERLAY": "rgba(0,0,0,0.60)",
    "BORDER_SUBTLE": "#2E2E35",
    "BORDER_STRONG": "#44444D",
    "BORDER_FOCUS": "#9B6DDB",
    "TEXT_PRIMARY": "#FFFFFF",
    "TEXT_SECONDARY": "#B4B4BD",
    "TEXT_MUTED": "#80808A",
    "TEXT_DISABLED": "#55555E",
    "TEXT_ON_ACCENT": "#FFFFFF",
    "ACCENT": "#9B6DDB",
    "ACCENT_HOVER": "#AE86E6",
    "ACCENT_PRESSED": "#8456C8",
    "ACCENT_SOFT": "rgba(155,109,219,0.18)",
    "SERIES_TWO": "#F4F4F5",
    "SERIES_THREE": "#4A4A55",
    "SUCCESS": "#2FA394",
    "SUCCESS_SOFT": "rgba(47,163,148,0.16)",
    "WARNING": "#E8B04A",
    "WARNING_SOFT": "rgba(232,176,74,0.16)",
    "DANGER": "#E5484D",
    "DANGER_SOFT": "rgba(229,72,77,0.16)",
    "INFO": "#4C8DFF",
    "INFO_SOFT": "rgba(76,141,255,0.16)",
}

RADIUS = {
    "window": 14,
    "card": 16,
    "button": 10,
    "input": 10,
    "nav": 10,
    "chip": 999,
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

TYPOGRAPHY = {
    "ui": '"Inter", "Segoe UI Variable", "Segoe UI"',
    "display": 28,
    "h1": 20,
    "h2": 16,
    "body": 13,
    "caption": 11,
    "metric": 26,
    "render_font": "Arial",
    "render_size": 22,
}

DEFAULT_RENDER = {
    "style_key": "sent_blue",
    "theme": "light",
    "font": "Arial",
    "font_size": 22,
    "max_width": 700,
    "alignment": "left",
    "transparent": True,
    "scale": 1,
    "padding_x": 8,
    "padding_y": 5,
    "thumbnail_fit": "off",
}

THUMBNAIL_FITS = [
    ("off", "Original size"),
    ("wide", "Wide (1.91:1)"),
    ("square", "Square"),
]

THUMBNAIL_RATIOS = {"off": 0.0, "wide": 1.91, "square": 1.0}

RENDER_FONTS = ["Segoe UI", "Arial", "Calibri", "Verdana", "Tahoma", "Georgia"]

# Resolution order used by the reference renderer when a font is missing:
# arial.ttf -> segoeui.ttf -> calibri.ttf -> PIL's built-in default.
RENDER_FONT_FALLBACKS = ["Arial", "Segoe UI", "Calibri"]


@dataclass(frozen=True)
class BubblePreset:
    key: str
    label: str
    fill: str
    text: str
    plain: bool = False
    dark: bool = False


BUBBLE_PRESETS: dict[str, BubblePreset] = {
    "sent_blue": BubblePreset("sent_blue", "Sent · Messenger blue", "#0084FF", "#FFFFFF"),
    "sent_violet": BubblePreset("sent_violet", "Sent · Violet", "#8E5CF7", "#FFFFFF"),
    "sent_dark": BubblePreset("sent_dark", "Sent · Dark theme", "#0866FF", "#FFFFFF", dark=True),
    "received_light": BubblePreset(
        "received_light", "Received · Light", "#E4E6EB", "#050505"
    ),
    "received_dark": BubblePreset(
        "received_dark", "Received · Dark", "#303030", "#E4E6EB", dark=True
    ),
    "plain_light": BubblePreset(
        "plain_light", "Plain text · Light", "transparent", "#050505", plain=True
    ),
    "plain_dark": BubblePreset(
        "plain_dark", "Plain text · Dark", "transparent", "#E4E6EB", plain=True, dark=True
    ),
}

STYLE_LABELS = {key: preset.label for key, preset in BUBBLE_PRESETS.items()}

CHART_COLORS = [
    COLORS["ACCENT"],
    COLORS["SERIES_TWO"],
    COLORS["SERIES_THREE"],
    COLORS["SUCCESS"],
    COLORS["INFO"],
]


def qcolor(value: str | QColor, alpha: int | None = None) -> QColor:
    if isinstance(value, QColor):
        color = QColor(value)
    elif value.startswith("rgba("):
        inner = value[value.index("(") + 1 : value.rindex(")")]
        parts = [part.strip() for part in inner.split(",")]
        color = QColor(int(parts[0]), int(parts[1]), int(parts[2]))
        rgba_alpha = float(parts[3])
        color.setAlpha(round(rgba_alpha * 255))
    else:
        color = QColor(value)
    if alpha is not None:
        color.setAlpha(alpha)
    return color


def token(name: str) -> str:
    return COLORS[name]


def render_theme_background(theme: str) -> str:
    return "#FFFFFF" if theme == "light" else COLORS["BG_CANVAS"]


def value(name: str, default: Any = None) -> Any:
    return COLORS.get(name, default)
