from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import qVersion

from textpic.__version__ import APP_NAME, VERSION
from textpic.context import AppContext
from textpic.services.hotkeys import normalize_hotkey, parse_hotkey
from textpic.services.settings_service import RETENTION_OPTIONS
from textpic.theme import tokens
from textpic.ui.pages.common import (
    ScrollPage,
    SettingRow,
    ToggleRow,
    card_layout,
    divider_line,
    hint,
    make_card,
)
from textpic.ui.widgets.controls import (
    Chip,
    DangerButton,
    GhostButton,
    LinkButton,
    PrimaryButton,
)
from textpic.ui.widgets.hotkey_box import HotkeyBox


RETENTION_LABELS = {
    30: "Keep for 30 days",
    90: "Keep for 90 days",
    365: "Keep for 1 year",
    0: "Keep forever",
}


class SettingsPage(ScrollPage):
    settings_saved = Signal()
    hotkeys_changed = Signal()
    profile_changed = Signal()
    toast = Signal(str, str)

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context
        self._build()
        self.load_from_settings()

    def _build(self) -> None:
        profile_card = make_card()
        profile_layout = card_layout(profile_card, (18, 16, 18, 16), 12)
        profile_layout.addWidget(self._card_title("Profile & workspace"))
        profile_layout.addWidget(
            hint("Shown on your dashboard and used to personalize TextPic Studio.")
        )
        profile_fields = QHBoxLayout()
        profile_fields.setSpacing(16)
        self.display_input = QLineEdit()
        self.display_input.setPlaceholderText("Your display name")
        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("e.g. Sales & Support")
        self.workspace_input = QLineEdit()
        self.workspace_input.setPlaceholderText("Workspace name")
        profile_fields.addWidget(
            self._field("Display name", self.display_input), 1
        )
        profile_fields.addWidget(self._field("Role", self.role_input), 1)
        profile_fields.addWidget(
            self._field("Workspace", self.workspace_input), 1
        )
        profile_layout.addLayout(profile_fields)
        profile_footer = QHBoxLayout()
        profile_footer.addStretch(1)
        profile_save = PrimaryButton("Save profile")
        profile_save.clicked.connect(self.save_profile)
        profile_footer.addWidget(profile_save)
        profile_layout.addLayout(profile_footer)
        self.body.addWidget(profile_card)

        hotkey_card = make_card()
        hotkey_layout = card_layout(hotkey_card, (18, 16, 18, 16), 10)
        hotkey_header = QHBoxLayout()
        hotkey_header.addWidget(self._card_title("Global hotkeys"))
        hotkey_header.addStretch(1)
        hotkey_header.addWidget(Chip("Works in any app", "accent"))
        hotkey_layout.addLayout(hotkey_header)
        hotkey_layout.addWidget(
            hint(
                "Click a field and press a key combination. Render and paste work on the "
                "app you are using and do not open this window. Add a fallback when "
                "another app already owns the primary shortcut."
            )
        )
        self.render_hotkey = HotkeyBox()
        self.render_hotkey_alt = HotkeyBox(allow_empty=True)
        self.paste_hotkey = HotkeyBox()
        self.paste_hotkey_alt = HotkeyBox(allow_empty=True)
        self.combo_hotkey = HotkeyBox(allow_empty=True)
        self.combo_hotkey_alt = HotkeyBox(allow_empty=True)
        hotkey_layout.addWidget(
            SettingRow(
                "Render & copy",
                "Renders the selected text from any app, or the current message when "
                "TextPic Studio is focused, and copies the PNG.",
                self._hotkey_pair(self.render_hotkey, self.render_hotkey_alt),
            )
        )
        hotkey_layout.addWidget(divider_line())
        hotkey_layout.addWidget(
            SettingRow(
                "Paste image",
                "Sends Ctrl+V to the app you were using, without opening TextPic Studio.",
                self._hotkey_pair(self.paste_hotkey, self.paste_hotkey_alt),
            )
        )
        hotkey_layout.addWidget(divider_line())
        hotkey_layout.addWidget(
            SettingRow(
                "Open composer",
                "Brings TextPic Studio forward and focuses the editor.",
                self._hotkey_pair(self.combo_hotkey, self.combo_hotkey_alt),
            )
        )
        hotkey_footer = QHBoxLayout()
        self.hotkey_status = QLabel("")
        self.hotkey_status.setObjectName("StatusText")
        hotkey_footer.addWidget(self.hotkey_status, 1)
        hotkey_save = PrimaryButton("Apply hotkeys")
        hotkey_save.clicked.connect(self.save_hotkeys)
        hotkey_footer.addWidget(hotkey_save)
        hotkey_layout.addLayout(hotkey_footer)
        self.body.addWidget(hotkey_card)

        behavior_card = make_card()
        behavior_layout = card_layout(behavior_card, (18, 16, 18, 16), 10)
        behavior_layout.addWidget(self._card_title("Startup & behavior"))
        self.start_windows = ToggleRow(
            "Start TextPic Studio with Windows",
            "Adds a per-user startup entry. You can remove it any time.",
        )
        self.start_minimized = ToggleRow(
            "Start minimized to tray",
            "Keep the app out of the way while hotkeys stay active.",
        )
        self.close_to_tray = ToggleRow(
            "Closing keeps TextPic Studio running",
            "Use the tray menu or Quit to exit completely.",
        )
        self.sound = ToggleRow(
            "Play a sound when a message is rendered",
            "A subtle confirmation for successful actions.",
        )
        self.auto_clear = ToggleRow(
            "Clear the editor after a successful paste",
            "Useful when you compose a new reply for every message.",
        )
        self.capture_mode = ToggleRow(
            "Capture selected text with the composer hotkey",
            "Experimental: copies the selected text from the active app before opening the editor.",
        )
        for index, row in enumerate(
            (
                self.start_windows,
                self.start_minimized,
                self.close_to_tray,
                self.sound,
                self.auto_clear,
                self.capture_mode,
            )
        ):
            behavior_layout.addWidget(row)
            if index < 5:
                behavior_layout.addWidget(divider_line())

        behavior_layout.addWidget(divider_line())
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 2000)
        self.delay_spin.setSingleStep(10)
        self.delay_spin.setSuffix(" ms")
        behavior_layout.addWidget(
            SettingRow(
                "Paste delay",
                "Wait before sending Ctrl+V so the target app can settle.",
                self.delay_spin,
            )
        )
        self.retention_combo = QComboBox()
        for days in RETENTION_OPTIONS:
            self.retention_combo.addItem(RETENTION_LABELS[days], days)
        behavior_layout.addWidget(
            SettingRow(
                "History retention",
                "Pinned messages are always kept.",
                self.retention_combo,
            )
        )
        behavior_footer = QHBoxLayout()
        self.behavior_status = QLabel("")
        self.behavior_status.setObjectName("StatusText")
        behavior_footer.addWidget(self.behavior_status, 1)
        restore = GhostButton("Restore defaults")
        restore.clicked.connect(self.restore_defaults)
        behavior_footer.addWidget(restore)
        behavior_save = PrimaryButton("Save behavior")
        behavior_save.clicked.connect(self.save_behavior)
        behavior_footer.addWidget(behavior_save)
        behavior_layout.addLayout(behavior_footer)
        self.body.addWidget(behavior_card)

        data_card = make_card()
        data_layout = card_layout(data_card, (18, 16, 18, 16), 10)
        data_layout.addWidget(self._card_title("Data & privacy"))
        data_layout.addWidget(
            hint(
                "Messages, templates, settings and rendered PNGs are stored locally. "
                "Nothing is uploaded."
            )
        )
        self.data_path = QLabel(str(self.context.data_dir))
        self.data_path.setObjectName("Hint")
        self.data_path.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.data_path.setWordWrap(True)
        data_layout.addWidget(self.data_path)
        data_actions = QHBoxLayout()
        data_actions.setSpacing(8)
        open_folder = GhostButton("Open data folder", "folder")
        open_folder.clicked.connect(self.open_data_folder)
        export_settings = GhostButton("Export settings", "download")
        export_settings.clicked.connect(self.export_settings)
        import_settings = GhostButton("Import settings", "upload")
        import_settings.clicked.connect(self.import_settings)
        export_history = GhostButton("Export history CSV", "export")
        export_history.clicked.connect(self.export_history)
        data_actions.addWidget(open_folder)
        data_actions.addWidget(export_settings)
        data_actions.addWidget(import_settings)
        data_actions.addWidget(export_history)
        data_actions.addStretch(1)
        data_layout.addLayout(data_actions)
        data_layout.addWidget(divider_line())
        danger_row = QHBoxLayout()
        danger_text = QVBoxLayout()
        danger_text.setSpacing(2)
        danger_title = QLabel("Erase all local data")
        danger_title.setObjectName("ToggleTitle")
        danger_text.addWidget(danger_title)
        danger_text.addWidget(
            hint("Deletes history, images, templates and settings. This cannot be undone.")
        )
        danger_row.addLayout(danger_text, 1)
        wipe = DangerButton("Wipe data", "trash")
        wipe.clicked.connect(self.wipe_data)
        danger_row.addWidget(wipe)
        data_layout.addLayout(danger_row)
        self.body.addWidget(data_card)

        about_card = make_card()
        about_layout = card_layout(about_card, (18, 16, 18, 16), 8)
        about_header = QHBoxLayout()
        about_header.addWidget(self._card_title("About"))
        about_header.addStretch(1)
        about_header.addWidget(Chip(f"v{VERSION}", "muted"))
        about_layout.addLayout(about_header)
        about_layout.addWidget(
            hint(
                f"{APP_NAME} turns messages into polished chat bubble images and pastes "
                "them with a global hotkey."
            )
        )
        about_layout.addWidget(hint(f"Qt {qVersion()} · Python 3.12 · Windows x64"))
        link = LinkButton("Qt and third-party license information")
        link.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://www.qt.io/licensing"))
        )
        about_layout.addWidget(link, 0, Qt.AlignmentFlag.AlignLeft)
        self.body.addWidget(about_card)
        self.body.addStretch(1)

    @staticmethod
    def _card_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("CardTitle")
        return label

    @staticmethod
    def _field(label_text: str, control: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        label = QLabel(label_text)
        label.setObjectName("FormLabel")
        layout.addWidget(label)
        layout.addWidget(control)
        return wrapper

    @staticmethod
    def _hotkey_pair(primary: HotkeyBox, fallback: HotkeyBox) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        fallback.setToolTip(
            "Optional fallback. Use it when another app already owns the primary shortcut."
        )
        for label_text, box in (("Primary", primary), ("Fallback", fallback)):
            column = QVBoxLayout()
            column.setSpacing(3)
            label = QLabel(label_text)
            label.setObjectName("FormLabel")
            column.addWidget(label)
            box.setMinimumWidth(132)
            column.addWidget(box)
            layout.addLayout(column)
        return wrapper

    def load_from_settings(self) -> None:
        settings = self.context.settings
        self.display_input.setText(str(settings.get("display_name")))
        self.role_input.setText(str(settings.get("role")))
        self.workspace_input.setText(str(settings.get("workspace_name")))
        self.render_hotkey.set_sequence(str(settings.get("hotkey_render")), emit=False)
        self.render_hotkey_alt.set_sequence(
            str(settings.get("hotkey_render_alt")), emit=False
        )
        self.paste_hotkey.set_sequence(str(settings.get("hotkey_paste")), emit=False)
        self.paste_hotkey_alt.set_sequence(
            str(settings.get("hotkey_paste_alt")), emit=False
        )
        self.combo_hotkey.set_sequence(str(settings.get("hotkey_combo")), emit=False)
        self.combo_hotkey_alt.set_sequence(
            str(settings.get("hotkey_combo_alt")), emit=False
        )
        self.start_windows.setChecked(self.context.autostart.is_enabled())
        self.start_minimized.setChecked(settings.get_bool("start_minimized"))
        self.close_to_tray.setChecked(settings.get_bool("close_to_tray"))
        self.sound.setChecked(settings.get_bool("sound"))
        self.auto_clear.setChecked(settings.get_bool("auto_clear"))
        self.capture_mode.setChecked(settings.get_bool("capture_mode"))
        self.delay_spin.setValue(settings.get_int("paste_delay_ms"))
        index = self.retention_combo.findData(settings.get_int("retention_days"))
        self.retention_combo.setCurrentIndex(max(0, index))
        self.data_path.setText(str(self.context.data_dir))

    def _set_status(self, label: QLabel, text: str, tone: str) -> None:
        label.setText(text)
        label.setProperty("tone", tone)
        label.style().unpolish(label)
        label.style().polish(label)

    def save_profile(self) -> None:
        self.context.settings.update(
            {
                "display_name": self.display_input.text().strip() or "You",
                "role": self.role_input.text().strip(),
                "workspace_name": self.workspace_input.text().strip()
                or "My Workspace",
            }
        )
        self.profile_changed.emit()
        self.settings_saved.emit()
        self.toast.emit("success", "Profile saved.")

    def save_hotkeys(self) -> None:
        sequences = {
            "render": [self.render_hotkey.sequence(), self.render_hotkey_alt.sequence()],
            "paste": [self.paste_hotkey.sequence(), self.paste_hotkey_alt.sequence()],
            "combo": [self.combo_hotkey.sequence(), self.combo_hotkey_alt.sequence()],
        }
        try:
            for values in sequences.values():
                for sequence in values:
                    if sequence:
                        parse_hotkey(sequence)
        except ValueError as exc:
            self._set_status(self.hotkey_status, str(exc), "danger")
            return
        if not sequences["render"][0] or not sequences["paste"][0]:
            self._set_status(
                self.hotkey_status,
                "Render and paste primary hotkeys cannot be empty.",
                "danger",
            )
            return
        normalized = {
            key: [normalize_hotkey(value) if value else "" for value in values]
            for key, values in sequences.items()
        }
        nonempty = [
            value for values in normalized.values() for value in values if value
        ]
        if len(set(nonempty)) != len(nonempty):
            self._set_status(
                self.hotkey_status,
                "Each primary and fallback hotkey must be different.",
                "danger",
            )
            return
        template_hotkeys = {
            record.hotkey for record in self.context.templates.list_all() if record.hotkey
        }
        conflicts = [value for value in nonempty if value in template_hotkeys]
        if conflicts:
            self._set_status(
                self.hotkey_status,
                f"{conflicts[0]} is already used by a template.",
                "danger",
            )
            return
        self.context.settings.update(
            {
                "hotkey_render": normalized["render"][0],
                "hotkey_render_alt": normalized["render"][1],
                "hotkey_paste": normalized["paste"][0],
                "hotkey_paste_alt": normalized["paste"][1],
                "hotkey_combo": normalized["combo"][0],
                "hotkey_combo_alt": normalized["combo"][1],
            }
        )
        self.render_hotkey.set_sequence(normalized["render"][0], emit=False)
        self.render_hotkey_alt.set_sequence(normalized["render"][1], emit=False)
        self.paste_hotkey.set_sequence(normalized["paste"][0], emit=False)
        self.paste_hotkey_alt.set_sequence(normalized["paste"][1], emit=False)
        self.combo_hotkey.set_sequence(normalized["combo"][0], emit=False)
        self.combo_hotkey_alt.set_sequence(normalized["combo"][1], emit=False)
        self.hotkeys_changed.emit()
        self._set_status(self.hotkey_status, "Hotkeys applied.", "success")
        self.toast.emit("success", "Global hotkeys updated.")

    def save_behavior(self) -> None:
        start_with_windows = self.start_windows.isChecked()
        try:
            self.context.autostart.set_enabled(start_with_windows)
        except OSError as exc:
            self._set_status(
                self.behavior_status,
                f"Could not update startup: {exc}",
                "danger",
            )
            return
        self.context.settings.update(
            {
                "start_with_windows": start_with_windows,
                "start_minimized": self.start_minimized.isChecked(),
                "close_to_tray": self.close_to_tray.isChecked(),
                "sound": self.sound.isChecked(),
                "auto_clear": self.auto_clear.isChecked(),
                "capture_mode": self.capture_mode.isChecked(),
                "paste_delay_ms": self.delay_spin.value(),
                "retention_days": int(self.retention_combo.currentData()),
            }
        )
        self.context.paste.set_delay(self.delay_spin.value())
        self.context.workflow.apply_retention()
        self.settings_saved.emit()
        self._set_status(self.behavior_status, "Behavior saved.", "success")
        self.toast.emit("success", "Behavior settings saved.")

    def restore_defaults(self) -> None:
        answer = QMessageBox.question(
            self,
            "Restore default settings",
            "Reset profile, hotkeys and behavior settings to their defaults? "
            "History and templates are kept.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.context.settings.reset()
        try:
            self.context.autostart.set_enabled(False)
        except OSError:
            pass
        self.load_from_settings()
        self.hotkeys_changed.emit()
        self.profile_changed.emit()
        self.settings_saved.emit()
        self.toast.emit("success", "Default settings restored.")

    def open_data_folder(self) -> None:
        self.context.data_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.context.data_dir)))

    def export_settings(self) -> None:
        default_path = str(self.context.data_dir / "settings-export.json")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export settings", default_path, "JSON file (*.json)"
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            self.context.settings.export_json(Path(path))
        except OSError as exc:
            self.toast.emit("error", f"Could not export settings: {exc}")
            return
        self.toast.emit("success", "Settings exported.")

    def import_settings(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import settings", str(self.context.data_dir), "JSON file (*.json)"
        )
        if not path:
            return
        try:
            imported = self.context.settings.import_json(Path(path))
        except (OSError, ValueError) as exc:
            self.toast.emit("error", f"Could not import settings: {exc}")
            return
        self.load_from_settings()
        if "start_with_windows" in imported:
            try:
                self.context.autostart.set_enabled(
                    self.context.settings.get_bool("start_with_windows")
                )
            except OSError:
                pass
        self.context.paste.set_delay(self.context.settings.get_int("paste_delay_ms"))
        self.hotkeys_changed.emit()
        self.profile_changed.emit()
        self.settings_saved.emit()
        self.toast.emit("success", f"Imported {len(imported)} settings.")

    def export_history(self) -> None:
        records = self.context.history.fetch(0, 100000)
        default_path = str(self.context.data_dir / "message-history.csv")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export message history", default_path, "CSV file (*.csv)"
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "ID",
                        "Created",
                        "Text",
                        "Style",
                        "Theme",
                        "Font",
                        "Font size",
                        "Scale",
                        "Status",
                        "Pasted",
                        "Pinned",
                    ]
                )
                for record in records:
                    writer.writerow(
                        [
                            record.id,
                            record.created_utc,
                            record.text,
                            record.style_key,
                            record.theme,
                            record.font,
                            record.font_size,
                            record.scale,
                            record.status,
                            record.pasted_utc or "",
                            1 if record.pinned else 0,
                        ]
                    )
        except OSError as exc:
            self.toast.emit("error", f"Could not export history: {exc}")
            return
        self.toast.emit("success", f"Exported {len(records):,} messages.")

    def wipe_data(self) -> None:
        text, accepted = QInputDialog.getText(
            self,
            "Wipe all data",
            "This permanently deletes messages, images, templates and settings.\n"
            "Type DELETE to continue:",
            QLineEdit.EchoMode.Normal,
            "",
        )
        if not accepted or text.strip().upper() != "DELETE":
            return
        try:
            self.context.autostart.set_enabled(False)
        except OSError:
            pass
        self.context.workflow.wipe_data()
        self.load_from_settings()
        self.context.paste.set_delay(self.context.settings.get_int("paste_delay_ms"))
        self.hotkeys_changed.emit()
        self.profile_changed.emit()
        self.settings_saved.emit()
        self.toast.emit("success", "All local data was erased.")
