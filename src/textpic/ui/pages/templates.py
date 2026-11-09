from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from textpic.context import AppContext
from textpic.services.template_repo import TemplateRecord
from textpic.ui.dialogs import (
    PlaceholderDialog,
    TemplateDialog,
    fill_placeholders,
    placeholder_keys,
)
from textpic.ui.pages.common import (
    ScrollPage,
    card_layout,
    divider_line,
    hint,
    make_card,
)
from textpic.ui.widgets.controls import (
    Chip,
    GhostButton,
    IconButton,
    PrimaryButton,
)
from textpic.ui.widgets.empty_state import EmptyState
from textpic.ui.widgets.keycap import Keycap


def build_template_text(
    template: TemplateRecord, parent: QWidget | None = None
) -> str | None:
    keys = placeholder_keys(template.body)
    if not keys:
        return template.body
    dialog = PlaceholderDialog(template.body, keys, template.title, parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return fill_placeholders(template.body, dialog.values())


class TemplateCard(QFrame):
    use_requested = Signal(int)
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, record: TemplateRecord, parent: QWidget | None = None):
        super().__init__(parent)
        self.record = record
        self.setObjectName("TemplateCard")
        self.setMinimumHeight(218)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = card_layout(self, (18, 16, 18, 14), 10)

        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel(record.title)
        title.setObjectName("CardTitle")
        header.addWidget(title)
        header.addStretch(1)
        if record.hotkey:
            header.addWidget(Keycap(record.hotkey))
        delete = IconButton("trash", "Delete template", "TEXT_MUTED")
        delete.clicked.connect(lambda: self.delete_requested.emit(self.record.id))
        header.addWidget(delete)
        layout.addLayout(header)

        body = QLabel(record.body)
        body.setObjectName("Muted")
        body.setWordWrap(True)
        body.setMinimumHeight(58)
        body.setMaximumHeight(76)
        body.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        layout.addWidget(body)

        keys = placeholder_keys(record.body)
        chips = QHBoxLayout()
        chips.setSpacing(6)
        if keys:
            for key in keys[:4]:
                chips.addWidget(Chip("{" + key + "}", "info"))
            if len(keys) > 4:
                chips.addWidget(Chip(f"+{len(keys) - 4}", "muted"))
        else:
            chips.addWidget(Chip("No placeholders", "muted"))
        chips.addStretch(1)
        layout.addLayout(chips)
        layout.addWidget(divider_line())

        actions = QHBoxLayout()
        actions.setSpacing(8)
        use = PrimaryButton("Use template", "play")
        use.setProperty("size", "sm")
        use.clicked.connect(lambda: self.use_requested.emit(self.record.id))
        edit_button = GhostButton("Edit", "edit")
        edit_button.setProperty("size", "sm")
        edit_button.clicked.connect(lambda: self.edit_requested.emit(self.record.id))
        actions.addWidget(use)
        actions.addWidget(edit_button)
        actions.addStretch(1)
        layout.addLayout(actions)


class TemplatesPage(ScrollPage):
    compose_requested = Signal(str)
    templates_changed = Signal()
    toast = Signal(str, str)

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(180)
        self._search_timer.timeout.connect(self.refresh)
        self._build()
        self.refresh()

    def _build(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("SearchField")
        self.search.setPlaceholderText("Search quick replies…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda: self._search_timer.start())
        self.search.setMaximumWidth(380)
        toolbar.addWidget(self.search)
        toolbar.addStretch(1)
        self.count_label = QLabel("")
        self.count_label.setObjectName("Hint")
        toolbar.addWidget(self.count_label)
        new_button = PrimaryButton("New template", "plus")
        new_button.clicked.connect(self.create_template)
        toolbar.addWidget(new_button)
        self.body.addLayout(toolbar)

        intro = make_card()
        intro_layout = card_layout(intro, (18, 14, 18, 14), 8)
        intro_row = QHBoxLayout()
        intro_row.setSpacing(12)
        intro_text = QVBoxLayout()
        intro_text.setSpacing(2)
        intro_title = QLabel("Reply faster with reusable messages")
        intro_title.setObjectName("CardTitle")
        intro_text.addWidget(intro_title)
        intro_text.addWidget(
            hint(
                "Use {name}, {product} and {price} placeholders. "
                "Assign a global hotkey to paste a reply without opening the app."
            )
        )
        intro_row.addLayout(intro_text, 1)
        intro_row.addWidget(Chip("Ctrl+Alt+1 – 9", "accent"))
        intro_layout.addLayout(intro_row)
        self.body.addWidget(intro)

        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)
        self.body.addWidget(self.grid_host)
        self.empty = EmptyState(
            "templates",
            "No matching templates",
            "Create a reusable reply or clear the search.",
            "New template",
        )
        self.empty.action_clicked.connect(self._empty_action)
        self.body.addWidget(self.empty)
        self.body.addStretch(1)

    def refresh(self) -> None:
        self._clear_grid()
        search = self.search.text().strip().lower()
        records = self.context.templates.list_all()
        if search:
            records = [
                record
                for record in records
                if search in record.title.lower() or search in record.body.lower()
            ]
        self.count_label.setText(
            f"{len(records)} template{'s' if len(records) != 1 else ''}"
        )
        if not records:
            self.grid_host.setVisible(False)
            self.empty.setVisible(True)
            if search:
                self.empty.title.setText("No matching templates")
                self.empty.body.setText("Try a different search term.")
                self.empty.action.setText("Clear search")
            else:
                self.empty.title.setText("No templates yet")
                self.empty.body.setText(
                    "Create a reusable reply and assign a global hotkey."
                )
                self.empty.action.setText("New template")
            return
        self.empty.setVisible(False)
        self.grid_host.setVisible(True)
        for index, record in enumerate(records):
            card = TemplateCard(record)
            card.use_requested.connect(self._use_template)
            card.edit_requested.connect(self._edit_template)
            card.delete_requested.connect(self._delete_template)
            self.grid.addWidget(card, index // 2, index % 2)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

    def _clear_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _empty_action(self) -> None:
        if self.search.text().strip():
            self.search.clear()
            self.refresh()
        else:
            self.create_template()

    def _record(self, template_id: int) -> TemplateRecord | None:
        return self.context.templates.get(template_id)

    def _use_template(self, template_id: int) -> None:
        record = self._record(template_id)
        if record is None:
            return
        text = build_template_text(record, self.window())
        if text is None:
            return
        self.compose_requested.emit(text)

    def create_template(self) -> None:
        dialog = TemplateDialog(parent=self.window())
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        title, body, hotkey = dialog.data()
        try:
            self.context.templates.create(title, body, hotkey)
        except ValueError as exc:
            QMessageBox.warning(self, "Could not save template", str(exc))
            return
        self.toast.emit("success", "Template created.")
        self.templates_changed.emit()
        self.refresh()

    def _edit_template(self, template_id: int) -> None:
        record = self._record(template_id)
        if record is None:
            return
        dialog = TemplateDialog(record.title, record.body, record.hotkey, self.window())
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        title, body, hotkey = dialog.data()
        try:
            self.context.templates.update(template_id, title, body, hotkey)
        except ValueError as exc:
            QMessageBox.warning(self, "Could not save template", str(exc))
            return
        self.toast.emit("success", "Template updated.")
        self.templates_changed.emit()
        self.refresh()

    def _delete_template(self, template_id: int) -> None:
        record = self._record(template_id)
        if record is None:
            return
        answer = QMessageBox.question(
            self,
            "Delete template",
            f"Delete “{record.title}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.context.templates.delete(template_id)
        self.toast.emit("success", "Template deleted.")
        self.templates_changed.emit()
        self.refresh()
