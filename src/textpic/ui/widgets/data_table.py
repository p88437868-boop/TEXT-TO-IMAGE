from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QTableView, QWidget


class DataTable(QTableView):
    context_menu_requested = Signal(object, QPoint)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(40)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.horizontalHeader().setStretchLastSection(False)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.customContextMenuRequested.connect(
            lambda point: self.context_menu_requested.emit(self.indexAt(point), point)
        )

    def set_row_height(self, height: int) -> None:
        self.verticalHeader().setDefaultSectionSize(height)

    def selected_ids(self) -> list[int]:
        rows = {index.row() for index in self.selectionModel().selectedRows()}
        return sorted(rows)
