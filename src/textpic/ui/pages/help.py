from __future__ import annotations

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from textpic.__version__ import VERSION
from textpic.context import AppContext
from textpic.paths import log_path
from textpic.ui.pages.common import (
    ScrollPage,
    card_layout,
    divider_line,
    hint,
    make_card,
)
from textpic.ui.widgets.controls import Chip, GhostButton, LinkButton
from textpic.ui.widgets.keycap import Keycap


class HelpPage(ScrollPage):
    navigate = Signal(str)

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context
        self._build()

    def _build(self) -> None:
        hero = make_card()
        hero_layout = card_layout(hero, (22, 20, 22, 20), 10)
        hero_row = QHBoxLayout()
        hero_row.setSpacing(18)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(4)
        title = QLabel("Make any message look ready to send.")
        title.setObjectName("PageTitle")
        hero_text.addWidget(title)
        hero_text.addWidget(
            hint(
                "TextPic Studio renders chat-style message images locally, copies them "
                "as images, then pastes them into the app you are already using."
            )
        )
        hero_row.addLayout(hero_text, 1)
        hero_row.addWidget(Chip(f"Version {VERSION}", "accent"))
        hero_layout.addLayout(hero_row)
        self.body.addWidget(hero)

        steps = make_card()
        steps_layout = card_layout(steps, (18, 16, 18, 16), 12)
        steps_layout.addWidget(self._title("Quick start"))
        for number, title_text, body in (
            (
                "1",
                "Compose your message",
                "Open Compose and type the reply. Emoji, line breaks and placeholders are supported.",
            ),
            (
                "2",
                f"Render & copy with {self._display_hotkey('hotkey_render', 'hotkey_render_alt')}",
                "The app renders the selected text from the app you are using, or the "
                "current message when TextPic Studio is focused. The window stays hidden.",
            ),
            (
                "3",
                f"Paste with {self._display_hotkey('hotkey_paste', 'hotkey_paste_alt')}",
                "Switch to your chat app, then use the primary or fallback shortcut. "
                "TextPic Studio sends Ctrl+V for you.",
            ),
        ):
            row = QHBoxLayout()
            row.setSpacing(12)
            badge = QLabel(number)
            badge.setObjectName("StepBadge")
            badge.setFixedSize(28, 28)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
            text_column = QVBoxLayout()
            text_column.setSpacing(2)
            step_title = QLabel(title_text)
            step_title.setObjectName("ToggleTitle")
            text_column.addWidget(step_title)
            text_column.addWidget(hint(body))
            row.addLayout(text_column, 1)
            steps_layout.addLayout(row)
            if number != "3":
                steps_layout.addWidget(divider_line())
        self.body.addWidget(steps)

        hotkeys = make_card()
        hotkey_layout = card_layout(hotkeys, (18, 16, 18, 16), 12)
        hotkeys_header = QHBoxLayout()
        hotkeys_header.addWidget(self._title("Keyboard shortcuts"))
        hotkeys_header.addStretch(1)
        customize = LinkButton("Customize →")
        customize.clicked.connect(lambda: self.navigate.emit("settings"))
        hotkeys_header.addWidget(customize)
        hotkey_layout.addLayout(hotkeys_header)
        hotkey_layout.addWidget(
            hint("Global shortcuts work while another application is focused.")
        )
        for key, action, description in (
            (
                self._display_hotkey("hotkey_render", "hotkey_render_alt"),
                "Render & copy",
                "Render the selected text from any app and copy the PNG, without opening "
                "TextPic Studio.",
            ),
            (
                self._display_hotkey("hotkey_paste", "hotkey_paste_alt"),
                "Paste image",
                "Send Ctrl+V to the focused app without stealing focus.",
            ),
            (
                self._display_hotkey("hotkey_combo", "hotkey_combo_alt"),
                "Open composer",
                "Bring TextPic Studio forward and focus the editor.",
            ),
            (
                "Ctrl+Alt+1…9",
                "Quick template",
                "Use a saved reply that has a template hotkey assigned.",
            ),
            ("Ctrl+1…7", "Switch pages", "Move between the main sections of the app."),
        ):
            row = QHBoxLayout()
            row.setSpacing(12)
            row.addWidget(Keycap(str(key)), 0, Qt.AlignmentFlag.AlignTop)
            text_column = QVBoxLayout()
            text_column.setSpacing(2)
            action_label = QLabel(action)
            action_label.setObjectName("ToggleTitle")
            text_column.addWidget(action_label)
            text_column.addWidget(hint(description))
            row.addLayout(text_column, 1)
            hotkey_layout.addLayout(row)
        self.body.addWidget(hotkeys)

        placeholders = make_card()
        placeholder_layout = card_layout(placeholders, (18, 16, 18, 16), 10)
        placeholder_layout.addWidget(self._title("Template placeholders"))
        placeholder_layout.addWidget(
            hint(
                "Placeholders are filled in when you use a template. They are plain "
                "text, so they also work in any language."
            )
        )
        for token, example in (
            ("{name}", "The customer or recipient name."),
            ("{product}", "The product or service you are discussing."),
            ("{price}", "A price, quote or offer."),
        ):
            row = QHBoxLayout()
            row.setSpacing(10)
            row.addWidget(Chip(token, "info"), 0, Qt.AlignmentFlag.AlignTop)
            row.addWidget(hint(example), 1)
            placeholder_layout.addLayout(row)
        self.body.addWidget(placeholders)

        troubleshooting = make_card()
        trouble_layout = card_layout(troubleshooting, (18, 16, 18, 16), 10)
        trouble_layout.addWidget(self._title("Troubleshooting"))
        for heading, body in (
            (
                f"{self._display_hotkey('hotkey_paste', 'hotkey_paste_alt')} does not paste into an elevated app",
                "Windows blocks synthetic input between different integrity levels. "
                "Press Ctrl+V manually, or run TextPic Studio as administrator.",
            ),
            (
                "A hotkey does not work",
                "Another app may already own that combination. Open Settings → Global "
                "hotkeys and choose a different combo.",
            ),
            (
                "An image is missing from history",
                "The PNG may have been moved or deleted outside TextPic Studio. "
                "The message text remains available in the database.",
            ),
            (
                "The app is still running after I close it",
                "Close-to-tray is enabled by default. Use Quit in the tray menu, or turn "
                "off the behavior in Settings.",
            ),
        ):
            text_column = QVBoxLayout()
            text_column.setSpacing(2)
            heading_label = QLabel(heading)
            heading_label.setObjectName("ToggleTitle")
            heading_label.setWordWrap(True)
            text_column.addWidget(heading_label)
            text_column.addWidget(hint(body))
            trouble_layout.addLayout(text_column)
            trouble_layout.addWidget(divider_line())
        self.body.addWidget(troubleshooting)

        footer = make_card()
        footer_layout = card_layout(footer, (18, 16, 18, 16), 10)
        footer_row = QHBoxLayout()
        footer_text = QVBoxLayout()
        footer_text.setSpacing(2)
        privacy_title = QLabel("Private by design")
        privacy_title.setObjectName("CardTitle")
        footer_text.addWidget(privacy_title)
        footer_text.addWidget(
            hint(
                "All content stays under your Windows profile. No account, cloud sync "
                "or network connection is required."
            )
        )
        footer_row.addLayout(footer_text, 1)
        open_folder = GhostButton("Open data folder", "folder")
        open_folder.clicked.connect(self.open_data_folder)
        open_log = GhostButton("View log", "info")
        open_log.clicked.connect(self.open_log)
        footer_row.addWidget(open_folder)
        footer_row.addWidget(open_log)
        footer_layout.addLayout(footer_row)
        self.body.addWidget(footer)
        self.body.addStretch(1)

    @staticmethod
    def _title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("CardTitle")
        return label

    def _display_hotkey(self, primary_key: str, fallback_key: str) -> str:
        primary = str(self.context.settings.get(primary_key) or "").strip()
        fallback = str(self.context.settings.get(fallback_key) or "").strip()
        if primary and fallback:
            return f"{primary} / {fallback}"
        return primary or fallback or "—"

    def open_data_folder(self) -> None:
        self.context.data_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.context.data_dir)))

    def open_log(self) -> None:
        path = log_path()
        if not path.exists():
            log_path().touch(exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
