from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from textpic.theme import tokens
from textpic.theme.icons import ICONS
from textpic.ui.widgets.empty_state import EmptyState


class ChartCard(QFrame):
    exported = Signal(str)
    export_failed = Signal(str)

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        value: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("Card")
        self._title = title
        self._chart_view: QWidget | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        title_column = QVBoxLayout()
        title_column.setSpacing(1)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("CardSubtitle")
        self.subtitle_label.setVisible(bool(subtitle))
        self.value_label = QLabel(value)
        self.value_label.setObjectName("ChartValue")
        self.value_label.setVisible(bool(value))
        title_column.addWidget(self.title_label)
        title_column.addWidget(self.subtitle_label)
        title_column.addWidget(self.value_label)
        header.addLayout(title_column)
        header.addStretch(1)
        self.header_actions = QHBoxLayout()
        self.header_actions.setSpacing(4)
        header.addLayout(self.header_actions)

        self.export_button = QToolButton()
        self.export_button.setIcon(ICONS.icon("export", "TEXT_MUTED", 18))
        self.export_button.setToolTip("Export chart as PNG")
        self.export_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_button.setFixedSize(32, 32)
        menu = QMenu(self.export_button)
        export_action = QAction("Export chart as PNG…", menu)
        export_action.triggered.connect(self._export_png)
        menu.addAction(export_action)
        self.export_button.setMenu(menu)
        self.header_actions.addWidget(self.export_button)
        layout.addLayout(header)

        self.legend_layout = QHBoxLayout()
        self.legend_layout.setSpacing(14)
        layout.addLayout(self.legend_layout)

        self.stack = QStackedWidget()
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)
        self.empty_state = EmptyState(
            "analytics",
            "No data for this period",
            "Render a message or switch the date range.",
        )
        self.stack.addWidget(self.body)
        self.stack.addWidget(self.empty_state)
        layout.addWidget(self.stack, 1)

    def add_header_widget(self, widget: QWidget) -> None:
        self.header_actions.addWidget(widget)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)
        self.value_label.setVisible(bool(value))

    def set_subtitle(self, subtitle: str) -> None:
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))

    def set_legend(self, items: list[tuple[str, str]]) -> None:
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for label, color_token in items:
            wrapper = QWidget()
            row = QHBoxLayout(wrapper)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            dot = QLabel()
            dot.setFixedSize(8, 8)
            color = tokens.COLORS.get(color_token, color_token)
            dot.setStyleSheet(
                f"background: {color}; border-radius: 4px;"
            )
            text = QLabel(label)
            text.setObjectName("ChartLegend")
            row.addWidget(dot)
            row.addWidget(text)
            self.legend_layout.addWidget(wrapper)
        self.legend_layout.addStretch(1)

    def set_chart_view(self, chart_view: QWidget) -> None:
        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._chart_view = chart_view
        self.body_layout.addWidget(chart_view)
        self.stack.setCurrentWidget(self.body)

    def show_empty(
        self,
        body: str = "Render a message or switch the date range.",
        title: str = "No data for this period",
    ) -> None:
        self.empty_state.title.setText(title)
        self.empty_state.body.setText(body)
        self.stack.setCurrentWidget(self.empty_state)

    def show_chart(self) -> None:
        if self._chart_view is not None:
            self.stack.setCurrentWidget(self.body)

    def _export_png(self) -> None:
        if self._chart_view is None:
            return
        pictures = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", self._title).strip("-").lower()
        default_path = str(Path(pictures or "") / f"textpic-{safe_name}.png")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export chart as PNG", default_path, "PNG image (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        pixmap = self._chart_view.grab()
        if pixmap.save(path, "PNG"):
            self.exported.emit(path)
        else:
            self.export_failed.emit("Could not save the chart PNG.")
