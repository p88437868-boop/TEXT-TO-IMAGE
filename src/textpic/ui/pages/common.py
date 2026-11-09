from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from textpic.ui.widgets.toggle import ToggleSwitch


PAGE_MARGINS = (26, 22, 26, 24)


def make_card(parent: QWidget | None = None) -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName("Card")
    return frame


def card_layout(
    card: QFrame,
    margins: tuple[int, int, int, int] = (18, 16, 18, 16),
    spacing: int = 12,
) -> QVBoxLayout:
    layout = QVBoxLayout(card)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def page_layout(page: QWidget) -> QVBoxLayout:
    layout = QVBoxLayout(page)
    layout.setContentsMargins(*PAGE_MARGINS)
    layout.setSpacing(18)
    return layout


def section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("SectionTitle")
    return label


def hint(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Hint")
    label.setWordWrap(True)
    return label


def muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Muted")
    label.setWordWrap(True)
    return label


class SegmentedControl(QWidget):
    changed = Signal(str)

    def __init__(
        self,
        options: list[tuple[str, str]],
        current: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._value = ""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for value, label in options:
            button = QPushButton(label)
            button.setProperty("role", "segment")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, selected=value: self._on_click(selected)
            )
            self.group.addButton(button)
            layout.addWidget(button)
            self._buttons[value] = button
        target = current if current in self._buttons else next(iter(self._buttons))
        self.set_value(target, emit=False)

    def _on_click(self, value: str) -> None:
        if self._value == value:
            return
        self._value = value
        self.changed.emit(value)

    def value(self) -> str:
        return self._value

    def set_value(self, value: str, emit: bool = False) -> None:
        button = self._buttons.get(value)
        if button is None:
            return
        self._value = value
        blocker = QSignalBlocker(self)
        button.setChecked(True)
        blocker.unblock()
        if emit:
            self.changed.emit(value)


class ToggleRow(QWidget):
    toggled = Signal(bool)

    def __init__(
        self,
        title: str,
        description: str = "",
        checked: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(14)
        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ToggleTitle")
        text_column.addWidget(self.title_label)
        if description:
            description_label = QLabel(description)
            description_label.setObjectName("Hint")
            description_label.setWordWrap(True)
            text_column.addWidget(description_label)
        self.switch = ToggleSwitch()
        self.switch.setChecked(checked)
        self.switch.toggled.connect(self.toggled.emit)
        layout.addLayout(text_column, 1)
        layout.addWidget(self.switch, 0, Qt.AlignmentFlag.AlignVCenter)

    def isChecked(self) -> bool:
        return self.switch.isChecked()

    def setChecked(self, checked: bool) -> None:
        blocker = QSignalBlocker(self.switch)
        self.switch.setChecked(checked)
        blocker.unblock()


class SettingRow(QWidget):
    def __init__(
        self,
        title: str,
        description: str = "",
        control: QWidget | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(14)
        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("ToggleTitle")
        text_column.addWidget(title_label)
        if description:
            description = QLabel(description)
            description.setObjectName("Hint")
            description.setWordWrap(True)
            text_column.addWidget(description)
        layout.addLayout(text_column, 1)
        if control is not None:
            layout.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)


class ScrollPage(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content = QWidget()
        self.content.setObjectName("PageContent")
        self.body = QVBoxLayout(self.content)
        self.body.setContentsMargins(*PAGE_MARGINS)
        self.body.setSpacing(18)
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll)


def divider_line() -> QFrame:
    frame = QFrame()
    frame.setObjectName("Divider")
    frame.setFixedHeight(1)
    return frame


def initials(name: str) -> str:
    pieces = [piece for piece in name.strip().split() if piece]
    if not pieces:
        return "?"
    if len(pieces) == 1:
        return pieces[0][:2].upper()
    return (pieces[0][0] + pieces[-1][0]).upper()
