from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QTimer, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from textpic.context import AppContext
from textpic.services.renderer import (
    MAX_TEXT_LENGTH,
    EmptyTextError,
    RenderConfig,
    RenderError,
)
from textpic.theme import tokens
from textpic.theme.icons import ICONS
from textpic.ui.pages.common import (
    SegmentedControl,
    ScrollPage,
    card_layout,
    divider_line,
    hint,
    make_card,
)
from textpic.ui.widgets.controls import (
    Chip,
    GhostButton,
    KeycapButton,
    LinkButton,
    PrimaryButton,
)
from textpic.ui.widgets.preview_pane import PreviewPane
from textpic.ui.widgets.toggle import ToggleSwitch


SCALE_OPTIONS = [(1.0, "1×"), (1.5, "1.5×"), (2.0, "2×"), (3.0, "3×")]


class ComposePage(ScrollPage):
    toast = Signal(str, str)

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(140)
        self._preview_timer.timeout.connect(self._update_preview)
        self._build()
        self.update_hotkey_labels()
        self._apply_defaults()
        self._update_character_count()
        self._update_preview()

    def _build(self) -> None:
        top = QHBoxLayout()
        top.setSpacing(18)

        editor_card = make_card()
        editor_layout = card_layout(editor_card, (18, 16, 18, 16), 12)
        editor_header = QHBoxLayout()
        title = QLabel("Your message")
        title.setObjectName("CardTitle")
        self.char_chip = Chip(f"0 / {MAX_TEXT_LENGTH}", "muted")
        clear_button = LinkButton("Clear")
        clear_button.clicked.connect(self.clear_text)
        editor_header.addWidget(title)
        editor_header.addStretch(1)
        editor_header.addWidget(self.char_chip)
        editor_header.addWidget(clear_button)
        editor_layout.addLayout(editor_header)

        self.editor = QTextEdit()
        self.editor.setObjectName("MessageEditor")
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText(
            "Type the message you want to send. Use emoji, line breaks and placeholders."
        )
        self.editor.setMinimumHeight(260)
        self.editor.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.editor.textChanged.connect(self._on_text_changed)
        editor_layout.addWidget(self.editor, 1)

        editor_footer = QHBoxLayout()
        editor_footer.setSpacing(8)
        editor_footer.addWidget(hint("Tip: keep it short — chat bubbles read best."))
        editor_footer.addStretch(1)
        self.hotkey_hint = hint("F6 renders · F9 pastes")
        editor_footer.addWidget(self.hotkey_hint)
        editor_layout.addLayout(editor_footer)
        top.addWidget(editor_card, 5)

        preview_card = make_card()
        preview_layout = card_layout(preview_card, (18, 16, 18, 16), 12)
        preview_header = QHBoxLayout()
        preview_title = QLabel("Live preview")
        preview_title.setObjectName("CardTitle")
        self.size_label = Chip("—", "muted")
        preview_header.addWidget(preview_title)
        preview_header.addStretch(1)
        preview_header.addWidget(self.size_label)
        preview_layout.addLayout(preview_header)

        self.preview = PreviewPane()
        self.preview.setMinimumHeight(260)
        preview_layout.addWidget(self.preview, 1)

        self.preview_error = QLabel("")
        self.preview_error.setObjectName("StatusText")
        self.preview_error.setProperty("tone", "danger")
        self.preview_error.setWordWrap(True)
        self.preview_error.setVisible(False)
        preview_layout.addWidget(self.preview_error)
        top.addWidget(preview_card, 4)
        self.body.addLayout(top, 1)

        options_card = make_card()
        options_layout = card_layout(options_card, (18, 14, 18, 16), 12)
        options_header = QHBoxLayout()
        options_title = QLabel("Style & format")
        options_title.setObjectName("CardTitle")
        reset_link = LinkButton("Reset options")
        reset_link.clicked.connect(self.reset_options)
        options_header.addWidget(options_title)
        options_header.addStretch(1)
        options_header.addWidget(reset_link)
        options_layout.addLayout(options_header)
        options_layout.addWidget(divider_line())

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        self.style_combo = QComboBox()
        self.style_combo.setMinimumWidth(200)
        for key, preset in tokens.BUBBLE_PRESETS.items():
            self.style_combo.addItem(
                QIcon(self._style_pixmap(preset.fill, preset.text, preset.plain)),
                preset.label,
                key,
            )
        self.style_combo.currentIndexChanged.connect(self._on_options_changed)
        grid.addWidget(self._field("Style preset", self.style_combo), 0, 0, 1, 2)

        self.font_combo = QComboBox()
        self.font_combo.addItems(tokens.RENDER_FONTS)
        self.font_combo.currentTextChanged.connect(self._on_options_changed)
        grid.addWidget(self._field("Font", self.font_combo), 0, 2)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(10, 48)
        self.size_spin.setSuffix(" px")
        self.size_spin.valueChanged.connect(self._on_options_changed)
        grid.addWidget(self._field("Text size", self.size_spin), 0, 3)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(120, 800)
        self.width_spin.setSingleStep(20)
        self.width_spin.setSuffix(" px")
        self.width_spin.valueChanged.connect(self._on_options_changed)
        grid.addWidget(self._field("Max width", self.width_spin), 0, 4)

        self.scale_combo = QComboBox()
        self.scale_combo.setToolTip(
            "1× keeps the PNG at the same pixel size as the message you typed. "
            "Higher values only produce a larger file."
        )
        for value, label in SCALE_OPTIONS:
            self.scale_combo.addItem(label, value)
        self.scale_combo.currentIndexChanged.connect(self._on_options_changed)
        grid.addWidget(self._field("Resolution", self.scale_combo), 0, 5)

        self.theme_control = SegmentedControl(
            [("light", "Light"), ("dark", "Dark")], "light"
        )
        self.theme_control.changed.connect(self._on_options_changed)
        grid.addWidget(self._field("Render theme", self.theme_control), 1, 0)

        self.align_control = SegmentedControl(
            [("left", "Left"), ("right", "Right")], "left"
        )
        self.align_control.changed.connect(self._on_options_changed)
        grid.addWidget(self._field("Alignment", self.align_control), 1, 1)

        transparency = QWidget()
        transparency_layout = QHBoxLayout(transparency)
        transparency_layout.setContentsMargins(0, 0, 0, 0)
        transparency_layout.setSpacing(10)
        self.transparent_switch = ToggleSwitch()
        self.transparent_switch.toggled.connect(self._on_options_changed)
        transparency_layout.addWidget(self.transparent_switch)
        transparency_layout.addWidget(QLabel("Transparent PNG"))
        transparency_layout.addStretch(1)
        grid.addWidget(self._field("Background", transparency), 1, 2, 1, 2)

        self.fit_combo = QComboBox()
        for value, label in tokens.THUMBNAIL_FITS:
            self.fit_combo.addItem(label, value)
        self.fit_combo.setToolTip(
            "Original size keeps the image exactly as large as the message. "
            "Wide/Square add padding so social thumbnails do not crop the sides."
        )
        self.fit_combo.currentIndexChanged.connect(self._on_options_changed)
        grid.addWidget(self._field("Thumbnail fit", self.fit_combo), 1, 4, 1, 2)

        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 2)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 1)
        grid.setColumnStretch(5, 1)
        options_layout.addLayout(grid)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        render_button = PrimaryButton("Render & copy", "sparkles")
        render_button.clicked.connect(self.render_current)
        self.render_action = KeycapButton(render_button, "F6")
        actions.addWidget(self.render_action)
        paste_button = GhostButton("Paste in app", "paste")
        paste_button.clicked.connect(self.paste_current)
        self.paste_action = KeycapButton(paste_button, "F9")
        actions.addWidget(self.paste_action)
        actions.addSpacing(6)
        copy_button = GhostButton("Copy image", "copy")
        copy_button.clicked.connect(self.copy_current)
        actions.addWidget(copy_button)
        save_button = GhostButton("Save PNG", "save")
        save_button.clicked.connect(self.save_png)
        actions.addWidget(save_button)
        actions.addStretch(1)
        self.action_status = QLabel("")
        self.action_status.setObjectName("StatusText")
        self.action_status.setProperty("tone", "success")
        actions.addWidget(self.action_status)
        options_layout.addLayout(actions)
        self.body.addWidget(options_card)

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
    def _style_pixmap(fill: str, text: str, plain: bool) -> QPixmap:
        pixmap = QPixmap(28, 28)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if plain:
            painter.setPen(tokens.qcolor(tokens.COLORS["BORDER_STRONG"]))
            painter.setBrush(tokens.qcolor(tokens.COLORS["SURFACE_INPUT"]))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(tokens.qcolor(fill))
        painter.drawRoundedRect(1, 5, 26, 18, 8, 8)
        font = painter.font()
        font.setPixelSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(tokens.qcolor(text))
        painter.drawText(1, 5, 26, 18, Qt.AlignmentFlag.AlignCenter, "Aa")
        painter.end()
        return pixmap

    def _apply_defaults(self) -> None:
        values = self.context.settings.render_defaults()
        self.font_combo.setCurrentText(str(values["font"]))
        self.size_spin.setValue(int(values["font_size"]))
        self.width_spin.setValue(int(values["max_width"]))
        self.theme_control.set_value(str(values["theme"]))
        self.align_control.set_value(str(values["alignment"]))
        self.transparent_switch.setChecked(bool(values["transparent"]))
        self._set_combo_data(self.fit_combo, values["thumbnail_fit"])
        self._set_combo_data(self.style_combo, values["style_key"])
        self._set_combo_data(self.scale_combo, float(values["scale"]))

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: object) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def update_hotkey_labels(self) -> None:
        render = str(self.context.settings.get("hotkey_render") or "F6")
        paste = str(self.context.settings.get("hotkey_paste") or "F9")
        self.render_action.set_key(render)
        self.paste_action.set_key(paste)
        self.hotkey_hint.setText(f"{render} renders · {paste} pastes")

    def config(self) -> RenderConfig:
        return RenderConfig(
            style_key=str(self.style_combo.currentData()),
            theme=self.theme_control.value(),
            font=self.font_combo.currentText(),
            font_size=self.size_spin.value(),
            max_width=self.width_spin.value(),
            alignment=self.align_control.value(),
            transparent=self.transparent_switch.isChecked(),
            scale=float(self.scale_combo.currentData()),
            padding_x=int(tokens.DEFAULT_RENDER["padding_x"]),
            padding_y=int(tokens.DEFAULT_RENDER["padding_y"]),
            thumbnail_fit=str(self.fit_combo.currentData()),
        )

    def _persist(self) -> None:
        self.context.settings.update(self.config().to_dict())

    def set_text(self, text: str, focus: bool = True) -> None:
        self.editor.setPlainText(text)
        self.editor.moveCursor(QTextCursor.MoveOperation.End)
        if focus:
            self.focus_editor()

    def text(self) -> str:
        return self.editor.toPlainText()

    def focus_editor(self) -> None:
        self.editor.setFocus(Qt.FocusReason.OtherFocusReason)

    def clear_text(self) -> None:
        self.editor.clear()
        self.action_status.clear()
        self.focus_editor()

    def clear_after_paste(self) -> None:
        if self.context.settings.get_bool("auto_clear"):
            self.editor.clear()

    def _on_text_changed(self) -> None:
        self._update_character_count()
        self._preview_timer.start()

    def _on_options_changed(self, *_args) -> None:
        self._preview_timer.start()

    def _update_character_count(self) -> None:
        length = len(self.editor.toPlainText())
        self.char_chip.setText(f"{length:,} / {MAX_TEXT_LENGTH:,}")
        if length > MAX_TEXT_LENGTH:
            self.char_chip.set_tone("danger")
        elif length > int(MAX_TEXT_LENGTH * 0.85):
            self.char_chip.set_tone("warning")
        else:
            self.char_chip.set_tone("muted")

    def _update_preview(self) -> None:
        text = self.editor.toPlainText()
        self.preview_error.setVisible(False)
        if not text.strip():
            self.preview.set_image(None)
            self.size_label.setText("—")
            self.size_label.set_tone("muted")
            return
        if len(text) > MAX_TEXT_LENGTH:
            self.preview.set_image(None)
            self.size_label.setText("Too long")
            self.size_label.set_tone("danger")
            self.preview_error.setText(
                f"Messages are limited to {MAX_TEXT_LENGTH:,} characters."
            )
            self.preview_error.setVisible(True)
            return
        try:
            result = self.context.renderer.render(text, self.config())
        except RenderError as exc:
            self.preview.set_image(None)
            self.size_label.setText("—")
            self.preview_error.setText(str(exc))
            self.preview_error.setVisible(True)
            return
        self.preview.set_image(result.image, self.config().scale)
        self.size_label.setText(f"{result.width} × {result.height}")
        self.size_label.set_tone("muted")

    def render_current(self) -> bool:
        text = self.editor.toPlainText()
        if not text.strip():
            self.toast.emit("error", "Type a message first.")
            self.focus_editor()
            return False
        try:
            self.context.workflow.render_text(text, self.config())
        except EmptyTextError:
            self.toast.emit("error", "Type a message first.")
            return False
        except RenderError as exc:
            self.toast.emit("error", str(exc))
            return False
        except Exception as exc:
            self.toast.emit("error", f"Could not render: {exc}")
            return False
        self._persist()
        self._update_preview()
        image = self.context.workflow.current_image
        if image is not None:
            self.preview.set_image(image, self.config().scale)
            self.size_label.setText(f"{image.width()} × {image.height()}")
        self.action_status.setText("Rendered and copied ✓")
        paste_hotkey = str(self.context.settings.get("hotkey_paste") or "F9")
        self.toast.emit(
            "success", f"Rendered and copied — press {paste_hotkey} to paste."
        )
        return True

    def paste_current(self) -> bool:
        if not self.context.workflow.paste_current():
            return False
        self.action_status.setText("Pasting…")
        return True

    def copy_current(self) -> bool:
        if not self.context.workflow.copy_current():
            return False
        self.action_status.setText("Copied ✓")
        return True

    def reset_options(self) -> None:
        self._apply_defaults()
        self._update_preview()

    def save_png(self) -> bool:
        text = self.editor.toPlainText()
        if not text.strip():
            self.toast.emit("error", "Type a message first.")
            return False
        try:
            result = self.context.renderer.render(text, self.config())
        except RenderError as exc:
            self.toast.emit("error", str(exc))
            return False
        pictures = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        folder = Path(pictures or str(Path.home())) / "TextPic Studio"
        folder.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^A-Za-z0-9]+", "-", text.strip())[:36].strip("-")
        name = slug or "message"
        default_path = folder / f"{name}-{datetime.now():%Y%m%d-%H%M%S}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save rendered message", str(default_path), "PNG image (*.png)"
        )
        if not path:
            return False
        if not path.lower().endswith(".png"):
            path += ".png"
        if result.image.save(path, "PNG"):
            self.action_status.setText("Saved ✓")
            self.toast.emit("success", f"Saved to {Path(path).name}.")
            return True
        self.toast.emit("error", "Could not save the PNG.")
        return False

    def paste_selected_text(self, text: str) -> None:
        if not text:
            self.toast.emit("error", "No selected text was captured.")
            return
        self.set_text(text)
