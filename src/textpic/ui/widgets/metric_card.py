from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from textpic.theme.icons import ICONS
from textpic.ui.widgets.controls import Chip, LinkButton, divider


class MetricCard(QFrame):
    report_requested = Signal()

    def __init__(
        self,
        icon_name: str,
        label: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setMinimumHeight(132)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)
        icon = QLabel()
        icon.setObjectName("MetricIcon")
        icon.setPixmap(ICONS.pixmap(icon_name, "ACCENT", 18))
        icon.setFixedSize(18, 18)
        label_widget = QLabel(label)
        label_widget.setObjectName("MetricLabel")
        self.trend = Chip("—", "muted")
        header.addWidget(icon)
        header.addWidget(label_widget)
        header.addStretch(1)
        header.addWidget(self.trend)
        layout.addLayout(header)

        self.value = QLabel("0")
        self.value.setObjectName("MetricValue")
        layout.addWidget(self.value)

        self.detail = QLabel("No activity yet")
        self.detail.setObjectName("MetricDetail")
        layout.addWidget(self.detail)
        layout.addStretch(1)
        layout.addWidget(divider())

        self.link = LinkButton("View Report →")
        self.link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.link.clicked.connect(self.report_requested.emit)
        layout.addWidget(self.link)

    def set_metric(
        self,
        value: str | int,
        trend: float,
        detail: str,
        trend_good_when_positive: bool = True,
    ) -> None:
        self.value.setText(str(value))
        arrow = "↗" if trend > 0 else ("↘" if trend < 0 else "→")
        formatted = f"{arrow} {abs(trend):.1f}%"
        self.trend.setText(formatted)
        if abs(trend) < 0.05:
            self.trend.set_tone("muted")
        else:
            is_good = trend > 0 if trend_good_when_positive else trend < 0
            self.trend.set_tone("success" if is_good else "danger")
        self.detail.setText(detail)
