from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from textpic.ui.widgets.controls import GhostButton, PrimaryButton


HOTKEY_CHOICES = ["None"] + [f"Ctrl+Alt+{index}" for index in range(1, 10)]


class TemplateDialog(QDialog):
    def __init__(
        self,
        title: str = "",
        body: str = "",
        hotkey: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Template")
        self.setModal(True)
        self.resize(520, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        heading = QLabel("New quick reply" if not title else "Edit quick reply")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        hint = QLabel(
            "Use {name}, {product} and {price} as placeholders. "
            "Global hotkeys work while another app is focused."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)
        self.title_input = QLineEdit(title)
        self.title_input.setPlaceholderText("e.g. Price quote")
        self.body_input = QTextEdit()
        self.body_input.setAcceptRichText(False)
        self.body_input.setPlainText(body)
        self.body_input.setPlaceholderText("Hi {name}, the {product} is {price}.")
        self.body_input.setMinimumHeight(210)
        self.hotkey_input = QComboBox()
        self.hotkey_input.addItems(HOTKEY_CHOICES)
        if hotkey and hotkey not in HOTKEY_CHOICES:
            self.hotkey_input.addItem(hotkey)
        self.hotkey_input.setCurrentText(hotkey or "None")
        form.addRow(self._label("Title"), self.title_input)
        form.addRow(self._label("Message"), self.body_input)
        form.addRow(self._label("Global hotkey"), self.hotkey_input)
        layout.addLayout(form)

        self.error = QLabel("")
        self.error.setObjectName("StatusText")
        self.error.setProperty("tone", "danger")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = GhostButton("Cancel")
        save = PrimaryButton("Save template")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    @staticmethod
    def _label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FormLabel")
        return label

    def _accept(self) -> None:
        if not self.title_input.text().strip():
            self.error.setText("Give the template a title.")
            return
        if not self.body_input.toPlainText().strip():
            self.error.setText("The template message cannot be empty.")
            return
        self.accept()

    def data(self) -> tuple[str, str, str | None]:
        hotkey = self.hotkey_input.currentText()
        return (
            self.title_input.text().strip(),
            self.body_input.toPlainText(),
            None if hotkey in ("", "None") else hotkey,
        )


class PlaceholderDialog(QDialog):
    def __init__(
        self,
        body: str,
        keys: list[str],
        title: str = "Quick reply",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(420, 240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        heading = QLabel("Fill in the placeholders")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        hint = QLabel(
            "These values are inserted into the message before it is rendered."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)
        self.inputs: dict[str, QLineEdit] = {}
        for key in keys:
            label = QLabel(key.capitalize())
            label.setObjectName("FormLabel")
            field = QLineEdit()
            field.setPlaceholderText(f"Enter {key}")
            self.inputs[key] = field
            form.addRow(label, field)
        layout.addLayout(form)
        layout.addStretch(1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = GhostButton("Cancel")
        insert = PrimaryButton("Render")
        cancel.clicked.connect(self.reject)
        insert.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(insert)
        layout.addLayout(buttons)

        if keys:
            self.inputs[keys[0]].setFocus(Qt.FocusReason.OtherFocusReason)

    def values(self) -> dict[str, str]:
        return {key: field.text().strip() for key, field in self.inputs.items()}


PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def placeholder_keys(body: str) -> list[str]:
    seen: list[str] = []
    for match in PLACEHOLDER_RE.finditer(body):
        key = match.group(1)
        if key not in seen:
            seen.append(key)
    return seen


def fill_placeholders(body: str, values: dict[str, str]) -> str:
    return PLACEHOLDER_RE.sub(lambda match: values.get(match.group(1), match.group(0)), body)
