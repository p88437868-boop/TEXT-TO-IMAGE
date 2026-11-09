from __future__ import annotations

import argparse
import math
import struct
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from textpic.theme import tokens


ICON_PATHS: dict[str, str] = {
    "dashboard": '<rect x="3" y="3" width="7" height="7" rx="1.8"/><rect x="14" y="3" width="7" height="7" rx="1.8"/><rect x="3" y="14" width="7" height="7" rx="1.8"/><rect x="14" y="14" width="7" height="7" rx="1.8"/>',
    "compose": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/><path d="m15 5 3 3"/>',
    "history": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/>',
    "templates": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 2h9a2 2 0 0 1 2 2v13"/><path d="M9 9h6M9 13h6M9 17h4"/>',
    "analytics": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "settings": '<circle cx="12" cy="12" r="3.2"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4v-.2a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.6 9a2.5 2.5 0 0 1 4.8 1c0 1.7-2.4 2-2.4 3.5"/><path d="M12 17.2h.01"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
    "export": '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
    "download": '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
    "upload": '<path d="M12 21V9"/><path d="m7 14 5-5 5 5"/><path d="M5 3h14"/>',
    "check": '<path d="m4 12 5 5L20 6"/>',
    "alert": '<path d="M10.3 3.7 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "copy": '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
    "paste": '<rect x="5" y="5" width="14" height="17" rx="2"/><path d="M9 5V3h6v2"/><path d="M9 10h6M9 14h6M9 18h4"/>',
    "trash": '<path d="M4 7h16"/><path d="M10 11v6M14 11v6"/><path d="m6 7 1 14h10l1-14"/><path d="M9 7V4h6v3"/>',
    "pin": '<path d="m15 4 5 5-3 1-4 4-1 5-3-3-4 4"/><path d="m5 19 4-4"/><path d="m14 3 7 7"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
    "zap": '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>',
    "sparkles": '<path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3Z"/><path d="m19 14 .8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14Z"/><path d="m5 14 .7 1.8 1.8.7-1.8.7L5 19l-.7-1.8-1.8-.7 1.8-.7L5 14Z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "keyboard": '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M6 14h.01M18 14h.01M9 14h6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
    "external": '<path d="M14 4h6v6"/><path d="m20 4-9 9"/><path d="M20 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h5"/>',
    "minimize": '<path d="M5 12h14"/>',
    "maximize": '<rect x="5" y="5" width="14" height="14" rx="1.5"/>',
    "restore": '<rect x="7" y="4" width="13" height="13" rx="1.5"/><path d="M4 8v11a1 1 0 0 0 1 1h11"/>',
    "close": '<path d="m6 6 12 12M18 6 6 18"/>',
    "folder": '<path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M7 3v6h9"/><path d="M7 21v-8h10v8"/>',
    "refresh": '<path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 4v5h5"/><path d="M4 13a8.1 8.1 0 0 0 15.5 2M20 20v-5h-5"/>',
    "play": '<path d="m7 4 13 8-13 8V4Z"/>',
    "shield": '<path d="M12 3 4.5 6v5.5c0 4.6 3.2 7.8 7.5 9.5 4.3-1.7 7.5-4.9 7.5-9.5V6L12 3Z"/><path d="m9 12 2 2 4-4"/>',
    "palette": '<path d="M12 3a9 9 0 1 0 0 18h1.5a1.8 1.8 0 0 0 0-3.6H12a2 2 0 0 1 0-4h3a6 6 0 0 0 0-12Z"/><circle cx="7.5" cy="10.5" r=".8"/><circle cx="10" cy="7" r=".8"/><circle cx="14" cy="7" r=".8"/>',
    "type": '<path d="M4 6h16M12 6v14M8 20h8"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
    "sliders": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
    "flame": '<path d="M12 22c4 0 7-3 7-7 0-5-4-8-4-12-2 1-3 3-3 5-1-1-2-2-2-4-3 3-5 6-5 11 0 4 3 7 7 7Z"/><path d="M12 22c2 0 3.5-1.4 3.5-3.3 0-2.2-2-3.5-3.5-5.7-1.5 2.2-3.5 3.5-3.5 5.7C8.5 20.6 10 22 12 22Z"/>',
    "layout": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18M9 9h12"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
}

COMPACT_ICONS = {
    "dashboard": '<rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/><rect x="13" y="13" width="8" height="8" rx="2"/>',
}

WINDOW_ICONS = {"minimize", "maximize", "restore", "close"}


def _svg(inner: str, stroke: str = "currentColor", fill: str = "none") -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        f'viewBox="0 0 24 24" fill="{fill}" stroke="{stroke}" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</svg>\n"
    )


def write_icons(assets: Path) -> None:
    icons = assets / "icons"
    ui = assets / "ui"
    icons.mkdir(parents=True, exist_ok=True)
    ui.mkdir(parents=True, exist_ok=True)
    for name, inner in ICON_PATHS.items():
        width = "1.6" if name in WINDOW_ICONS else "1.8"
        content = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
            f'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
            f"{inner}</svg>\n"
        )
        (icons / f"{name}.svg").write_text(content, encoding="utf-8")

    white = tokens.COLORS["TEXT_ON_ACCENT"]
    muted = tokens.COLORS["TEXT_MUTED"]
    (ui / "check_on.svg").write_text(
        _svg('<path d="m5 12 4 4L19 6"/>', white, "none"), encoding="utf-8"
    )
    (ui / "chevron_down.svg").write_text(
        _svg('<path d="m6 9 6 6 6-6"/>', muted), encoding="utf-8"
    )
    (ui / "chevron_up.svg").write_text(
        _svg('<path d="m6 15 6-6 6 6"/>', muted), encoding="utf-8"
    )


def write_logo(assets: Path) -> None:
    accent = tokens.COLORS["ACCENT"]
    accent_hover = tokens.COLORS["ACCENT_HOVER"]
    surface = tokens.COLORS["SURFACE_CARD"]
    content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{accent_hover}"/>
<stop offset="1" stop-color="{accent}"/>
</linearGradient>
<filter id="s" x="-30%" y="-30%" width="160%" height="160%">
<feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#000000" flood-opacity="0.35"/>
</filter>
</defs>
<rect width="512" height="512" rx="112" fill="{surface}"/>
<g filter="url(#s)">
<path d="M118 118h276a42 42 0 0 1 42 42v150a42 42 0 0 1-42 42H254l-82 60 16-60h-70a42 42 0 0 1-42-42V160a42 42 0 0 1 42-42Z" fill="url(#g)"/>
<rect x="166" y="196" width="180" height="20" rx="10" fill="#FFFFFF" opacity="0.96"/>
<rect x="166" y="242" width="132" height="20" rx="10" fill="#FFFFFF" opacity="0.82"/>
<rect x="166" y="288" width="86" height="20" rx="10" fill="#FFFFFF" opacity="0.62"/>
</g>
<circle cx="388" cy="132" r="46" fill="{tokens.COLORS['SUCCESS']}"/>
<path d="m367 132 14 14 28-30" fill="none" stroke="#FFFFFF" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''
    (assets / "logo.svg").write_text(content, encoding="utf-8")


def write_raster_assets(assets: Path, installer: Path) -> None:
    source = ROOT / "Icon.jfif"
    if not source.exists():
        raise FileNotFoundError("Icon.jfif is required")

    image = Image.open(source).convert("RGB")
    side = min(image.size)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    square = image.crop((left, top, left + side, top + side))
    square = square.resize((1024, 1024), Image.Resampling.LANCZOS)

    mask = Image.new("L", (1024, 1024), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, 1023, 1023), radius=168, fill=255)
    rounded = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    rounded.paste(square, (0, 0), mask)
    rounded.resize((512, 512), Image.Resampling.LANCZOS).save(assets / "brand.png")
    rounded.resize((256, 256), Image.Resampling.LANCZOS).save(assets / "logo.png")

    ico_sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    rounded.save(
        assets / "app.ico",
        format="ICO",
        sizes=[(size, size) for size in ico_sizes],
    )
    rounded.save(
        assets / "tray.ico",
        format="ICO",
        sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (48, 48), (64, 64)],
    )

    _write_checker(assets)
    _write_click(assets)
    _write_installer_art(installer, rounded)
    _write_license(installer)


def _write_checker(assets: Path) -> None:
    tile = 8
    image = Image.new("RGB", (tile * 2, tile * 2), tokens.COLORS["SURFACE_INPUT"])
    draw = ImageDraw.Draw(image)
    light = tokens.COLORS["SURFACE_CARD"]
    draw.rectangle((tile, 0, tile * 2 - 1, tile - 1), fill=light)
    draw.rectangle((0, tile, tile - 1, tile * 2 - 1), fill=light)
    image.save(assets / "checker.png")


def _write_click(assets: Path) -> None:
    sounds = assets / "sounds"
    sounds.mkdir(parents=True, exist_ok=True)
    rate = 44100
    duration = 0.055
    frames = bytearray()
    total = int(rate * duration)
    for index in range(total):
        progress = index / max(1, total - 1)
        envelope = (1.0 - progress) ** 2
        sample = math.sin(2 * math.pi * 720 * index / rate) * envelope
        value = int(max(-1.0, min(1.0, sample)) * 12000)
        frames.extend(struct.pack("<h", value))
    with wave.open(str(sounds / "click.wav"), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(bytes(frames))


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def _gradient(width: int, height: int) -> Image.Image:
    start = tokens.qcolor(tokens.COLORS["BG_GLOW_START"])
    mid = tokens.qcolor(tokens.COLORS["BG_CANVAS"])
    end = tokens.qcolor(tokens.COLORS["BG_GLOW_END"])
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            ratio = (x / max(1, width - 1) + y / max(1, height - 1)) / 2
            if ratio < 0.55:
                local = ratio / 0.55
                first, second = start, mid
            else:
                local = (ratio - 0.55) / 0.45
                first, second = mid, end
            color = tuple(
                round(first.red() + (second.red() - first.red()) * local)
                for _ in range(1)
            )
            red = round(first.red() + (second.red() - first.red()) * local)
            green = round(first.green() + (second.green() - first.green()) * local)
            blue = round(first.blue() + (second.blue() - first.blue()) * local)
            pixels[x, y] = (red, green, blue)
    return image


def _write_installer_art(installer: Path, brand: Image.Image) -> None:
    installer.mkdir(parents=True, exist_ok=True)
    banner = _gradient(493, 58)
    draw = ImageDraw.Draw(banner)
    icon = brand.resize((40, 40), Image.Resampling.LANCZOS)
    banner.paste(icon, (18, 9), icon)
    draw.text((72, 12), "TextPic Studio", font=_font(21, True), fill="#FFFFFF")
    draw.text(
        (72, 37),
        "Message images, ready to paste.",
        font=_font(9),
        fill=tokens.COLORS["TEXT_SECONDARY"],
    )
    banner.save(installer / "banner.bmp", format="BMP")

    dialog = _gradient(493, 312)
    draw = ImageDraw.Draw(dialog)
    glow = Image.new("RGBA", (493, 312), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((284, -100, 640, 240), fill=(*_rgb(tokens.COLORS["ACCENT"]), 45))
    glow_draw.ellipse((330, 180, 590, 430), fill=(*_rgb(tokens.COLORS["SUCCESS"]), 35))
    dialog = Image.alpha_composite(dialog.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(dialog)
    big = brand.resize((150, 150), Image.Resampling.LANCZOS)
    dialog.paste(big, (38, 48), big)
    draw.text((38, 222), "TextPic Studio", font=_font(26, True), fill="#FFFFFF")
    draw.text(
        (38, 258),
        "Render. Copy. Paste. Anywhere.",
        font=_font(11),
        fill=tokens.COLORS["TEXT_SECONDARY"],
    )
    dialog.save(installer / "dialog.bmp", format="BMP")


def _rgb(value: str) -> tuple[int, int, int]:
    color = tokens.qcolor(value)
    return color.red(), color.green(), color.blue()


def _write_license(installer: Path) -> None:
    accent = tokens.COLORS["ACCENT"]
    text = (
        r"{\rtf1\ansi\deff0"
        r"{\fonttbl{\f0 Segoe UI;}{\f1 Segoe UI Semibold;}}"
        r"\fs20\color0 "
        r"{\pard\qc\f1\fs36\b TextPic Studio\par}"
        r"{\pard\qc\f0\fs18 Version 1.0.3\par}\par"
        r"{\pard\f0\fs20\b License\b0\par}\par"
        r"{\pard\f0\fs18 TextPic Studio is provided as-is for personal and commercial use. "
        r"You may install and use this software on Windows devices that you own or control.\par}\par"
        r"{\pard\f0\fs20\b Data and privacy\b0\par}\par"
        r"{\pard\f0\fs18 All messages, templates, settings and rendered images are stored locally "
        r"on this computer. TextPic Studio does not create accounts and does not upload message content.\par}\par"
        r"{\pard\f0\fs20\b Third-party components\b0\par}\par"
        r"{\pard\f0\fs18 This application includes Qt and PySide6, distributed under the LGPLv3. "
        r"Source and license details are available from the Qt project.\par}\par"
        r"{\pard\f0\fs16\cf1 By continuing, you confirm that you have read and accept these terms.\par}"
        r"}"
    )
    installer.mkdir(parents=True, exist_ok=True)
    (installer / "license.rtf").write_text(text, encoding="ascii", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, default=ROOT / "assets")
    parser.add_argument("--installer", type=Path, default=ROOT / "installer")
    args = parser.parse_args()
    args.assets.mkdir(parents=True, exist_ok=True)
    write_icons(args.assets)
    write_logo(args.assets)
    write_raster_assets(args.assets, args.installer)
    print(f"Generated assets in {args.assets} and {args.installer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
