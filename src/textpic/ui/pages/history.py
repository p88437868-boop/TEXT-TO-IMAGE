from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPoint,
    QStandardPaths,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import QAction, QColor, QImage
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from textpic.context import AppContext
from textpic.services.history_repo import MessageFilters, MessageRecord
from textpic.theme import tokens
from textpic.ui.pages.common import (
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
from textpic.ui.widgets.data_table import DataTable
from textpic.ui.widgets.empty_state import EmptyState
from textpic.ui.widgets.preview_pane import PreviewPane


class MessageTableModel(QAbstractTableModel):
    HEADERS = ["Message", "Style", "Created", "Status"]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.records: list[MessageRecord] = []

    def set_records(self, records: list[MessageRecord]) -> None:
        self.beginResetModel()
        self.records = records
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.records)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        record = self.records[index.row()]
        column = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return record.preview
            if column == 1:
                return tokens.STYLE_LABELS.get(
                    record.style_key, record.style_key.replace("_", " ").title()
                )
            if column == 2:
                return record.local_time
            return "Pasted" if record.status == "pasted" else "Rendered"
        if role == Qt.ItemDataRole.ToolTipRole:
            return record.text[:800]
        if role == Qt.ItemDataRole.UserRole:
            return record
        if role == Qt.ItemDataRole.ForegroundRole:
            if column == 3:
                return QColor(
                    tokens.COLORS["SUCCESS"]
                    if record.status == "pasted"
                    else tokens.COLORS["TEXT_MUTED"]
                )
            if column == 0:
                return QColor(tokens.COLORS["TEXT_PRIMARY"])
        if role == Qt.ItemDataRole.TextAlignmentRole and column == 1:
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return None

    def record_at(self, row: int) -> MessageRecord | None:
        if 0 <= row < len(self.records):
            return self.records[row]
        return None


class HistoryPage(QWidget):
    navigate = Signal(str)
    toast = Signal(str, str)

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context
        self._selected_record: MessageRecord | None = None
        self._filters_active = False
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(220)
        self._search_timer.timeout.connect(self.refresh)
        self._build()
        self.refresh()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 22, 26, 24)
        outer.setSpacing(16)

        filter_card = make_card()
        filter_layout = card_layout(filter_card, (16, 12, 16, 12), 10)
        filter_header = QHBoxLayout()
        filter_title = QLabel("Find a message")
        filter_title.setObjectName("CardTitle")
        filter_header.addWidget(filter_title)
        filter_header.addStretch(1)
        self.reset_filters = LinkButton("Reset filters")
        self.reset_filters.clicked.connect(self._reset_filters)
        filter_header.addWidget(self.reset_filters)
        filter_layout.addLayout(filter_header)

        fields = QHBoxLayout()
        fields.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("SearchField")
        self.search.setPlaceholderText("Search message text or style…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda: self._search_timer.start())
        fields.addWidget(self.search, 1)

        self.date_filter = QComboBox()
        for label, days in [
            ("All time", 0),
            ("Today", 1),
            ("Last 7 days", 7),
            ("Last 30 days", 30),
            ("Last 90 days", 90),
        ]:
            self.date_filter.addItem(label, days)
        fields.addWidget(self.date_filter)

        self.style_filter = QComboBox()
        self.style_filter.addItem("All styles", "")
        for key, preset in tokens.BUBBLE_PRESETS.items():
            self.style_filter.addItem(preset.label, key)
        fields.addWidget(self.style_filter)

        self.pinned_only = QCheckBox("Pinned only")
        fields.addWidget(self.pinned_only)
        self.date_filter.currentIndexChanged.connect(self.refresh)
        self.style_filter.currentIndexChanged.connect(self.refresh)
        self.pinned_only.toggled.connect(self.refresh)
        filter_layout.addLayout(fields)
        outer.addWidget(filter_card)

        content = QHBoxLayout()
        content.setSpacing(16)
        table_card = make_card()
        table_layout = card_layout(table_card, (16, 14, 16, 14), 10)
        table_header = QHBoxLayout()
        table_title = QLabel("Message history")
        table_title.setObjectName("CardTitle")
        self.count_label = QLabel("0 messages")
        self.count_label.setObjectName("Hint")
        table_header.addWidget(table_title)
        table_header.addWidget(self.count_label)
        table_header.addStretch(1)
        self.delete_button = DangerButton("Delete selected", "trash")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_selected)
        clear_button = LinkButton("Clear all")
        clear_button.clicked.connect(self.clear_all)
        table_header.addWidget(self.delete_button)
        table_header.addWidget(clear_button)
        table_layout.addLayout(table_header)
        table_layout.addWidget(divider_line())

        self.table_stack = QStackedWidget()
        self.model = MessageTableModel(self)
        self.table = DataTable()
        self.table.setModel(self.model)
        self.table.set_row_height(48)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.selectionModel().selectionChanged.connect(self._selection_changed)
        self.table.doubleClicked.connect(lambda _index: self.paste_selected())
        self.table.context_menu_requested.connect(self._context_menu)
        self.empty = EmptyState(
            "history",
            "No matching messages",
            "Try a different search or clear the filters.",
            "Clear filters",
        )
        self.empty.action_clicked.connect(self._empty_action)
        self.table_stack.addWidget(self.table)
        self.table_stack.addWidget(self.empty)
        table_layout.addWidget(self.table_stack, 1)
        self.table_hint = hint("Select a message to preview it.")
        table_layout.addWidget(self.table_hint)
        content.addWidget(table_card, 1)

        detail_card = make_card()
        detail_card.setFixedWidth(350)
        detail_layout = card_layout(detail_card, (18, 16, 18, 16), 10)
        detail_header = QHBoxLayout()
        detail_title = QLabel("Preview")
        detail_title.setObjectName("CardTitle")
        self.status_chip = Chip("—", "muted")
        detail_header.addWidget(detail_title)
        detail_header.addStretch(1)
        detail_header.addWidget(self.status_chip)
        detail_layout.addLayout(detail_header)

        self.preview = PreviewPane()
        self.preview.set_placeholder(
            "No message selected",
            "Choose a message to preview its saved image.",
        )
        self.preview.setMinimumHeight(220)
        self.preview.setMaximumHeight(300)
        detail_layout.addWidget(self.preview)

        self.detail_text = QLabel("Select a message to preview it.")
        self.detail_text.setObjectName("Muted")
        self.detail_text.setWordWrap(True)
        self.detail_text.setMinimumHeight(48)
        self.detail_text.setMaximumHeight(86)
        detail_layout.addWidget(self.detail_text)

        self.meta_style = QLabel("")
        self.meta_style.setObjectName("Hint")
        self.meta_style.setWordWrap(True)
        self.meta_time = QLabel("")
        self.meta_time.setObjectName("Hint")
        self.meta_time.setWordWrap(True)
        detail_layout.addWidget(self.meta_style)
        detail_layout.addWidget(self.meta_time)
        detail_layout.addWidget(divider_line())

        action_grid = QHBoxLayout()
        action_grid.setSpacing(8)
        self.copy_button = GhostButton("Copy", "copy")
        self.copy_button.clicked.connect(self.copy_selected)
        self.paste_button = PrimaryButton("Paste", "paste")
        self.paste_button.clicked.connect(self.paste_selected)
        action_grid.addWidget(self.copy_button, 1)
        action_grid.addWidget(self.paste_button, 1)
        detail_layout.addLayout(action_grid)

        action_grid_two = QHBoxLayout()
        action_grid_two.setSpacing(8)
        self.save_button = GhostButton("Save PNG", "save")
        self.save_button.clicked.connect(self.save_selected)
        self.pin_button = GhostButton("Pin", "pin")
        self.pin_button.clicked.connect(self.toggle_pin)
        action_grid_two.addWidget(self.save_button, 1)
        action_grid_two.addWidget(self.pin_button, 1)
        detail_layout.addLayout(action_grid_two)

        self.delete_single = DangerButton("Delete message", "trash")
        self.delete_single.clicked.connect(self.delete_selected)
        detail_layout.addWidget(self.delete_single)
        detail_layout.addStretch(1)
        content.addWidget(detail_card)
        outer.addLayout(content, 1)

        self._set_detail_enabled(False)

    def _filters(self) -> MessageFilters:
        search = self.search.text().strip()
        days = int(self.date_filter.currentData() or 0)
        date_from = None
        if days == 1:
            date_from = date.today()
        elif days > 1:
            date_from = date.today() - timedelta(days=days - 1)
        return MessageFilters(
            search=search,
            date_from=date_from,
            pinned_only=self.pinned_only.isChecked(),
            style_key=str(self.style_filter.currentData() or ""),
        )

    def refresh(self) -> None:
        filters = self._filters()
        self._filters_active = bool(
            filters.search
            or filters.date_from
            or filters.pinned_only
            or filters.style_key
        )
        count = self.context.history.count(filters)
        records = self.context.history.fetch(0, 500, filters)
        self.model.set_records(records)
        self.count_label.setText(
            f"{count:,} message{'s' if count != 1 else ''}"
            + (" · showing first 500" if count > 500 else "")
        )
        if records:
            self.table_stack.setCurrentWidget(self.table)
            self.table_hint.setText(
                "Select a message to preview it. Double-click to paste."
            )
        else:
            self.table_stack.setCurrentWidget(self.empty)
            if self._filters_active:
                self.empty.title.setText("No matching messages")
                self.empty.body.setText("Try a different search or clear the filters.")
                self.empty.action.setText("Clear filters")
            else:
                self.empty.title.setText("No messages yet")
                self.empty.body.setText(
                    "Render your first message and it will appear here."
                )
                self.empty.action.setText("Compose a message")
            self.table_hint.setText("No messages match the current filters.")
        self._selected_record = None
        self._set_detail_enabled(False)
        self.preview.set_image(None)
        self.detail_text.setText("Select a message to preview it.")
        self.meta_style.clear()
        self.meta_time.clear()
        self.status_chip.setText("—")
        self.status_chip.set_tone("muted")
        self.delete_button.setEnabled(False)
        self._update_reset_link()

    def _update_reset_link(self) -> None:
        self.reset_filters.setEnabled(self._filters_active)

    def _empty_action(self) -> None:
        if self._filters_active:
            self._reset_filters()
        else:
            self.navigate.emit("compose")

    def _reset_filters(self) -> None:
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.date_filter.blockSignals(True)
        self.date_filter.setCurrentIndex(0)
        self.date_filter.blockSignals(False)
        self.style_filter.blockSignals(True)
        self.style_filter.setCurrentIndex(0)
        self.style_filter.blockSignals(False)
        self.pinned_only.blockSignals(True)
        self.pinned_only.setChecked(False)
        self.pinned_only.blockSignals(False)
        self.refresh()

    def _selection_changed(self, *_args) -> None:
        records = self._selected_records()
        self.delete_button.setEnabled(bool(records))
        if not records:
            self._selected_record = None
            self._set_detail_enabled(False)
            self.preview.set_image(None)
            self.detail_text.setText("Select a message to preview it.")
            self.meta_style.clear()
            self.meta_time.clear()
            self.status_chip.setText("—")
            self.status_chip.set_tone("muted")
            return
        record = records[0]
        self._selected_record = record
        self._set_detail_enabled(True)
        self.detail_text.setText(record.preview)
        self.meta_style.setText(
            f"{tokens.STYLE_LABELS.get(record.style_key, record.style_key)} · "
            f"{record.font_size}px · {record.scale:g}×"
        )
        self.meta_time.setText(f"Created {record.local_time}")
        self.status_chip.setText(
            "Pasted" if record.status == "pasted" else "Rendered"
        )
        self.status_chip.set_tone(
            "success" if record.status == "pasted" else "muted"
        )
        self.pin_button.setText("Unpin" if record.pinned else "Pin")
        self._load_preview(record)

    def _selected_records(self) -> list[MessageRecord]:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        return [
            record
            for row in rows
            if (record := self.model.record_at(row)) is not None
        ]

    @staticmethod
    def _load_image(record: MessageRecord) -> QImage | None:
        if not record.image_path:
            return None
        path = Path(record.image_path)
        if not path.exists():
            return None
        image = QImage(str(path))
        return None if image.isNull() else image

    def _load_preview(self, record: MessageRecord) -> None:
        image = self._load_image(record)
        self.preview.set_image(image, record.scale)
        if image is None:
            self.detail_text.setText("The saved PNG for this message is missing.")

    def _set_detail_enabled(self, enabled: bool) -> None:
        for widget in (
            self.copy_button,
            self.paste_button,
            self.save_button,
            self.pin_button,
            self.delete_single,
        ):
            widget.setEnabled(enabled)

    def copy_selected(self) -> None:
        records = self._selected_records()
        if records and self.context.workflow.copy_record(records[0]):
            self.toast.emit("success", "Copied the selected image.")

    def paste_selected(self) -> None:
        records = self._selected_records()
        if records:
            self.context.workflow.paste_record(records[0])

    def save_selected(self) -> None:
        records = self._selected_records()
        if not records:
            return
        record = records[0]
        image = self._load_image(record)
        if image is None:
            self.toast.emit("error", "The saved PNG for this message is missing.")
            return
        pictures = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        default_path = str(
            Path(pictures or str(Path.home()))
            / f"textpic-message-{record.id}.png"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Save message image", default_path, "PNG image (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        if image.save(path, "PNG"):
            self.toast.emit("success", "Saved the PNG.")
        else:
            self.toast.emit("error", "Could not save the PNG.")

    def toggle_pin(self) -> None:
        records = self._selected_records()
        if not records:
            return
        record = records[0]
        self.context.workflow.pin(record.id, not record.pinned)
        self.refresh()

    def delete_selected(self) -> None:
        records = self._selected_records()
        if not records:
            return
        answer = QMessageBox.question(
            self,
            "Delete messages",
            f"Delete {len(records)} selected message{'s' if len(records) != 1 else ''} "
            "and the saved PNGs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = self.context.workflow.delete_messages([r.id for r in records])
        self.toast.emit("success", f"Deleted {deleted} message{'s' if deleted != 1 else ''}.")
        self.refresh()

    def clear_all(self) -> None:
        count = self.context.history.count()
        if count == 0:
            self.toast.emit("info", "History is already empty.")
            return
        answer = QMessageBox.question(
            self,
            "Clear all history",
            f"Delete all {count} messages and their saved PNGs? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.context.workflow.clear_history()
        self.toast.emit("success", "History cleared.")
        self.refresh()

    def _context_menu(self, index: QModelIndex, point: QPoint) -> None:
        if not index.isValid():
            return
        if not self.table.selectionModel().isRowSelected(index.row(), QModelIndex()):
            self.table.selectRow(index.row())
        record = self.model.record_at(index.row())
        if record is None:
            return
        menu = QMenu(self)
        copy_action = QAction("Copy image", menu)
        paste_action = QAction("Paste into active app", menu)
        save_action = QAction("Save PNG…", menu)
        pin_action = QAction("Unpin" if record.pinned else "Pin", menu)
        delete_action = QAction("Delete…", menu)
        copy_action.triggered.connect(self.copy_selected)
        paste_action.triggered.connect(self.paste_selected)
        save_action.triggered.connect(self.save_selected)
        pin_action.triggered.connect(self.toggle_pin)
        delete_action.triggered.connect(self.delete_selected)
        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addAction(save_action)
        menu.addSeparator()
        menu.addAction(pin_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(point))
