from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from textpic.context import AppContext
from textpic.theme import tokens
from textpic.ui.pages.common import (
    ScrollPage,
    SegmentedControl,
    card_layout,
    hint,
    make_card,
)
from textpic.ui.widgets.chart_card import ChartCard
from textpic.ui.widgets.charting import (
    category_label,
    make_bar_chart,
    make_donut,
    make_hour_chart,
    make_line_chart,
)
from textpic.ui.widgets.controls import GhostButton
from textpic.ui.widgets.metric_card import MetricCard


class AnalyticsPage(ScrollPage):
    toast = Signal(str, str)

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context
        self._days = 7
        self._build()
        self.refresh()

    def _build(self) -> None:
        header = QHBoxLayout()
        header.setSpacing(12)
        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        title = QLabel("Your message activity")
        title.setObjectName("SectionTitle")
        text_column.addWidget(title)
        text_column.addWidget(
            hint("Understand how often you render, paste and reuse messages.")
        )
        header.addLayout(text_column, 1)
        self.range_control = SegmentedControl(
            [("7", "7 days"), ("30", "30 days"), ("90", "90 days")], "7"
        )
        self.range_control.changed.connect(self._range_changed)
        header.addWidget(self.range_control)
        export = GhostButton("Export CSV", "export")
        export.clicked.connect(self.export_csv)
        header.addWidget(export)
        self.body.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metric_rendered = MetricCard("image", "Rendered")
        self.metric_pasted = MetricCard("paste", "Pasted")
        self.metric_today = MetricCard("zap", "Today")
        self.metric_average = MetricCard("type", "Average length")
        for card in (
            self.metric_rendered,
            self.metric_pasted,
            self.metric_today,
            self.metric_average,
        ):
            metrics.addWidget(card, 1)
        self.body.addLayout(metrics)

        self.activity_card = ChartCard("Daily activity", "Rendered vs pasted")
        self.activity_card.setMinimumHeight(330)
        self.body.addWidget(self.activity_card)

        lower = QHBoxLayout()
        lower.setSpacing(16)
        self.style_card = ChartCard("Style mix", "Most-used message styles")
        self.style_card.setMinimumHeight(320)
        lower.addWidget(self.style_card, 1)
        self.hours_card = ChartCard("Peak hours", "When you render the most")
        self.hours_card.setMinimumHeight(320)
        lower.addWidget(self.hours_card, 1)
        self.body.addLayout(lower)

        self.length_card = ChartCard(
            "Message length", "Average characters per rendered message"
        )
        self.length_card.setMinimumHeight(310)
        self.body.addWidget(self.length_card)
        self.body.addStretch(1)

        for card in (
            self.metric_rendered,
            self.metric_pasted,
            self.metric_today,
            self.metric_average,
        ):
            card.report_requested.connect(self._report_clicked)

    def _range_changed(self, value: str) -> None:
        self._days = int(value)
        self.refresh()

    def _report_clicked(self) -> None:
        self.toast.emit("info", "Choose a range above to inspect your activity.")

    def refresh(self) -> None:
        overview = self.context.analytics.overview(self._days)
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
            f"characters · last {self._days} days",
        )
        self._refresh_activity()
        self._refresh_styles()
        self._refresh_hours()
        self._refresh_lengths()

    def _refresh_activity(self) -> None:
        data = self.context.analytics.daily_activity(self._days)
        total_created = sum(data["created"])
        total_pasted = sum(data["pasted"])
        self.activity_card.set_subtitle(
            f"Rendered vs pasted · last {self._days} days"
        )
        if total_created + total_pasted <= 0:
            self.activity_card.show_empty(
                "Render a message or adjust the date range.",
                "No activity in this period",
            )
            return
        dates = data["dates"]
        step = 1 if self._days <= 7 else (3 if self._days == 30 else 7)
        mode = "short" if self._days <= 7 else "date"
        categories = [
            category_label(item, index % step == 0 or index == len(dates) - 1, mode)
            for index, item in enumerate(dates)
        ]
        chart = make_bar_chart(
            categories,
            [
                ("Rendered", [float(v) for v in data["created"]], "ACCENT"),
                ("Pasted", [float(v) for v in data["pasted"]], "SUCCESS"),
            ],
        )
        chart.setMinimumHeight(230)
        self.activity_card.set_chart_view(chart)
        self.activity_card.set_legend(
            [("Rendered", "ACCENT"), ("Pasted", "SUCCESS")]
        )
        self.activity_card.set_value(
            f"{total_created:,} rendered · {total_pasted:,} pasted"
        )
        self.activity_card.show_chart()

    def _refresh_styles(self) -> None:
        styles = self.context.analytics.style_usage(self._days)
        if not styles:
            self.style_card.show_empty(
                "Styles appear after you render messages.",
                "No style data yet",
            )
            self.style_card.set_legend([])
            return
        chart = make_donut(
            [(item["label"], float(item["count"])) for item in styles]
        )
        token_names = [
            "ACCENT",
            "SERIES_TWO",
            "SERIES_THREE",
            "SUCCESS",
            "INFO",
        ]
        legend = [
            (item["label"], token_names[index % len(token_names)])
            for index, item in enumerate(styles)
        ]
        self.style_card.set_chart_view(chart)
        self.style_card.set_legend(legend)
        top = styles[0]
        self.style_card.set_value(
            f"{top['label']} · {top['count']:,} uses"
        )
        self.style_card.show_chart()

    def _refresh_hours(self) -> None:
        snapshot = self._snapshot()
        if snapshot["total_created"] <= 0:
            self.hours_card.show_empty(
                "Peak hours appear after you render messages.",
                "No hourly data yet",
            )
            return
        chart = make_hour_chart(snapshot["hours"])
        chart.setMinimumHeight(230)
        self.hours_card.set_chart_view(chart)
        self.hours_card.set_legend([("Rendered", "ACCENT")])
        peak_hour = max(range(24), key=lambda hour: snapshot["hours"][hour])
        self.hours_card.set_value(
            f"Peak: {peak_hour:02d}:00 · {snapshot['hours'][peak_hour]:,} messages"
        )
        self.hours_card.show_chart()

    def _refresh_lengths(self) -> None:
        snapshot = self._snapshot()
        if snapshot["total_created"] <= 0:
            self.length_card.show_empty(
                "Message length trends appear after you render messages.",
                "No length data yet",
            )
            return
        chart = make_line_chart(snapshot["days"], snapshot["average_length"])
        chart.setMinimumHeight(220)
        self.length_card.set_chart_view(chart)
        self.length_card.set_legend([("Average characters", "ACCENT")])
        average = snapshot["total_chars"] / max(1, snapshot["total_created"])
        self.length_card.set_value(f"Average: {average:.0f} characters")
        self.length_card.show_chart()

    def _snapshot(self) -> dict:
        end = date.today()
        start = end - timedelta(days=self._days - 1)
        return self.context.analytics.snapshot(start, end)

    def export_csv(self) -> None:
        snapshot = self._snapshot()
        pictures = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        default_path = str(
            Path(pictures or str(Path.home()))
            / f"textpic-analytics-{date.today():%Y%m%d}.csv"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Export analytics CSV", default_path, "CSV file (*.csv)"
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Date", "Rendered", "Pasted", "Average characters"])
                for index, day in enumerate(snapshot["days"]):
                    writer.writerow(
                        [
                            day.isoformat(),
                            snapshot["created"][index],
                            snapshot["pasted"][index],
                            round(snapshot["average_length"][index], 1),
                        ]
                    )
        except OSError as exc:
            self.toast.emit("error", f"Could not export CSV: {exc}")
            return
        self.toast.emit("success", "Analytics CSV exported.")
