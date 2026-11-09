from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from textpic.context import AppContext
from textpic.services.history_repo import MessageRecord
from textpic.ui.pages.common import (
    ScrollPage,
    card_layout,
    divider_line,
    hint,
    make_card,
)
from textpic.ui.widgets.chart_card import ChartCard
from textpic.ui.widgets.charting import category_label, make_bar_chart
from textpic.ui.widgets.controls import (
    Chip,
    GhostButton,
    IconButton,
    LinkButton,
    PrimaryButton,
)
from textpic.ui.widgets.empty_state import EmptyState
from textpic.ui.widgets.keycap import Keycap
from textpic.ui.widgets.metric_card import MetricCard


class RecentRow(QFrame):
    copy_requested = Signal(object)
    paste_requested = Signal(object)

    def __init__(self, record: MessageRecord, parent: QWidget | None = None):
        super().__init__(parent)
        self.record = record
        self.setObjectName("RecentRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        preview = QLabel(record.preview)
        preview.setObjectName("RecentPreview")
        text_column.addWidget(preview)
        metadata = QLabel(f"{record.style_key.replace('_', ' ')} · {record.local_time}")
        metadata.setObjectName("Hint")
        text_column.addWidget(metadata)
        layout.addLayout(text_column, 1)

        status = Chip("Pasted", "success") if record.status == "pasted" else Chip(
            "Rendered", "muted"
        )
        layout.addWidget(status)

        copy_button = IconButton("copy", "Copy image")
        copy_button.clicked.connect(lambda: self.copy_requested.emit(self.record))
        paste_button = IconButton("paste", "Paste image")
        paste_button.clicked.connect(lambda: self.paste_requested.emit(self.record))
        layout.addWidget(copy_button)
        layout.addWidget(paste_button)


class TemplateQuickRow(QFrame):
    use_requested = Signal(int)

    def __init__(
        self,
        template_id: int,
        title: str,
        hotkey: str | None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("RecentRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 7, 0, 7)
        layout.setSpacing(8)
        label = QLabel(title)
        label.setObjectName("RecentPreview")
        layout.addWidget(label, 1)
        if hotkey:
            layout.addWidget(Keycap(hotkey))
        use = IconButton("play", "Use template", "ACCENT")
        use.clicked.connect(lambda: self.use_requested.emit(template_id))
        layout.addWidget(use)


class DashboardPage(ScrollPage):
    navigate = Signal(str)
    use_template = Signal(int)
    toast = Signal(str, str)

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context
        self._build()
        self.refresh()

    def _build(self) -> None:
        welcome = QHBoxLayout()
        welcome.setSpacing(12)
        title_column = QVBoxLayout()
        title_column.setSpacing(2)
        self.greeting = QLabel("Welcome back")
        self.greeting.setObjectName("PageTitle")
        self.date_label = QLabel("")
        self.date_label.setObjectName("PageSubtitle")
        title_column.addWidget(self.greeting)
        title_column.addWidget(self.date_label)
        welcome.addLayout(title_column, 1)
        analytics_button = GhostButton("View analytics", "analytics")
        analytics_button.clicked.connect(lambda: self.navigate.emit("analytics"))
        compose_button = PrimaryButton("New message", "plus")
        compose_button.clicked.connect(lambda: self.navigate.emit("compose"))
        welcome.addWidget(analytics_button)
        welcome.addWidget(compose_button)
        self.body.addLayout(welcome)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metric_rendered = MetricCard("image", "Rendered")
        self.metric_pasted = MetricCard("paste", "Pasted")
        self.metric_today = MetricCard("zap", "Today")
        self.metric_average = MetricCard("type", "Average length")
        self.metric_rendered.report_requested.connect(
            lambda: self.navigate.emit("analytics")
        )
        self.metric_pasted.report_requested.connect(
            lambda: self.navigate.emit("analytics")
        )
        self.metric_today.report_requested.connect(
            lambda: self.navigate.emit("history")
        )
        self.metric_average.report_requested.connect(
            lambda: self.navigate.emit("analytics")
        )
        for card in (
            self.metric_rendered,
            self.metric_pasted,
            self.metric_today,
            self.metric_average,
        ):
            metrics.addWidget(card, 1)
        self.body.addLayout(metrics)

        middle = QHBoxLayout()
        middle.setSpacing(16)
        self.activity_card = ChartCard(
            "Activity", "Rendered vs pasted · last 7 days"
        )
        self.activity_card.setMinimumHeight(330)
        activity_link = LinkButton("Open analytics →")
        activity_link.clicked.connect(lambda: self.navigate.emit("analytics"))
        self.activity_card.add_header_widget(activity_link)
        middle.addWidget(self.activity_card, 3)

        quick_card = make_card()
        quick_layout = card_layout(quick_card, (18, 16, 18, 16), 10)
        quick_header = QHBoxLayout()
        quick_title = QLabel("Quick actions")
        quick_title.setObjectName("CardTitle")
        quick_header.addWidget(quick_title)
        quick_header.addStretch(1)
        shortcut_link = LinkButton("Customize")
        shortcut_link.clicked.connect(lambda: self.navigate.emit("settings"))
        quick_header.addWidget(shortcut_link)
        quick_layout.addLayout(quick_header)

        self._add_shortcut(
            quick_layout,
            "F6",
            "Render & copy",
            "Turn the current message into a crisp PNG.",
        )
        self._add_shortcut(
            quick_layout,
            "F9",
            "Paste in the active app",
            "Sends Ctrl+V to your chat without stealing focus.",
        )
        self._add_shortcut(
            quick_layout,
            "F8",
            "Open the composer",
            "Jump straight back into the message editor.",
        )
        quick_layout.addStretch(1)
        quick_layout.addWidget(divider_line())
        privacy = QHBoxLayout()
        privacy.setSpacing(8)
        privacy.addWidget(Chip("100% local", "success"))
        privacy.addWidget(hint("Nothing leaves this computer."))
        privacy.addStretch(1)
        quick_layout.addLayout(privacy)
        middle.addWidget(quick_card, 2)
        self.body.addLayout(middle)

        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        recent_card = make_card()
        recent_layout = card_layout(recent_card, (18, 16, 18, 16), 10)
        recent_header = QHBoxLayout()
        recent_title = QLabel("Recent messages")
        recent_title.setObjectName("CardTitle")
        recent_link = LinkButton("View history →")
        recent_link.clicked.connect(lambda: self.navigate.emit("history"))
        recent_header.addWidget(recent_title)
        recent_header.addStretch(1)
        recent_header.addWidget(recent_link)
        recent_layout.addLayout(recent_header)
        self.recent_stack = QStackedWidget()
        self.recent_container = QWidget()
        self.recent_rows = QVBoxLayout(self.recent_container)
        self.recent_rows.setContentsMargins(0, 0, 0, 0)
        self.recent_rows.setSpacing(0)
        self.recent_empty = EmptyState(
            "history",
            "No messages yet",
            "Render your first message and it will show up here.",
            "Compose a message",
        )
        self.recent_empty.action_clicked.connect(lambda: self.navigate.emit("compose"))
        self.recent_stack.addWidget(self.recent_container)
        self.recent_stack.addWidget(self.recent_empty)
        recent_layout.addWidget(self.recent_stack, 1)
        bottom.addWidget(recent_card, 3)

        templates_card = make_card()
        templates_layout = card_layout(templates_card, (18, 16, 18, 16), 10)
        templates_header = QHBoxLayout()
        templates_title = QLabel("Quick templates")
        templates_title.setObjectName("CardTitle")
        templates_link = LinkButton("Manage →")
        templates_link.clicked.connect(lambda: self.navigate.emit("templates"))
        templates_header.addWidget(templates_title)
        templates_header.addStretch(1)
        templates_header.addWidget(templates_link)
        templates_layout.addLayout(templates_header)
        self.template_container = QWidget()
        self.template_rows = QVBoxLayout(self.template_container)
        self.template_rows.setContentsMargins(0, 0, 0, 0)
        self.template_rows.setSpacing(0)
        templates_layout.addWidget(self.template_container, 1)
        bottom.addWidget(templates_card, 2)
        self.body.addLayout(bottom)
        self.body.addStretch(1)

    @staticmethod
    def _add_shortcut(
        layout: QVBoxLayout, key: str, title: str, description: str
    ) -> None:
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(Keycap(key))
        text_column = QVBoxLayout()
        text_column.setSpacing(1)
        title_label = QLabel(title)
        title_label.setObjectName("RecentPreview")
        text_column.addWidget(title_label)
        text_column.addWidget(hint(description))
        row.addLayout(text_column, 1)
        layout.addLayout(row)
        layout.addWidget(divider_line())

    def refresh(self) -> None:
        name = str(self.context.settings.get("display_name") or "there")
        first = name.split()[0] if name.split() else name
        now = datetime.now()
        if now.hour < 5 or now.hour >= 18:
            greeting = "Good evening"
        elif now.hour < 12:
            greeting = "Good morning"
        else:
            greeting = "Good afternoon"
        self.greeting.setText(f"{greeting}, {first}.")
        self.date_label.setText(
            now.strftime("%A, %B %d · Your local message workspace")
        )
        overview = self.context.analytics.overview(7)
        self.metric_rendered.set_metric(
            overview["created"],
            overview["created_trend"],
            f"{overview['today']} today",
        )
        self.metric_pasted.set_metric(
            overview["pasted"],
            overview["pasted_trend"],
            f"{overview['pasted_today']} today",
        )
        self.metric_today.set_metric(
            overview["today"],
            overview["today_trend"],
            f"{overview['pasted_today']} pasted today",
        )
        self.metric_average.set_metric(
            f"{overview['average_length']:.0f}",
            overview["average_trend"],
            "characters · last 7 days",
        )

        activity = self.context.analytics.daily_activity(7)
        total = sum(activity["created"]) + sum(activity["pasted"])
        if total <= 0:
            self.activity_card.show_empty(
                "Render a message to start your activity graph.",
                "No activity yet",
            )
        else:
            categories = [
                category_label(item, True, "short") for item in activity["dates"]
            ]
            chart = make_bar_chart(
                categories,
                [
                    ("Rendered", [float(v) for v in activity["created"]], "ACCENT"),
                    ("Pasted", [float(v) for v in activity["pasted"]], "SUCCESS"),
                ],
                animate=False,
            )
            chart.setMinimumHeight(230)
            self.activity_card.set_chart_view(chart)
            self.activity_card.set_legend(
                [("Rendered", "ACCENT"), ("Pasted", "SUCCESS")]
            )
            self.activity_card.show_chart()

        recent = self.context.history.recent(4)
        self._clear_layout(self.recent_rows)
        if recent:
            for index, record in enumerate(recent):
                row = RecentRow(record)
                row.copy_requested.connect(self._copy_record)
                row.paste_requested.connect(self._paste_record)
                self.recent_rows.addWidget(row)
                if index < len(recent) - 1:
                    self.recent_rows.addWidget(divider_line())
            self.recent_rows.addStretch(1)
            self.recent_stack.setCurrentWidget(self.recent_container)
        else:
            self.recent_stack.setCurrentWidget(self.recent_empty)

        templates = self.context.templates.list_all()[:4]
        self._clear_layout(self.template_rows)
        for index, record in enumerate(templates):
            row = TemplateQuickRow(record.id, record.title, record.hotkey)
            row.use_requested.connect(self.use_template.emit)
            self.template_rows.addWidget(row)
            if index < len(templates) - 1:
                self.template_rows.addWidget(divider_line())
        self.template_rows.addStretch(1)

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _copy_record(self, record: MessageRecord) -> None:
        if self.context.workflow.copy_record(record):
            self.toast.emit("success", "Copied the saved image.")

    def _paste_record(self, record: MessageRecord) -> None:
        self.context.workflow.paste_record(record)
