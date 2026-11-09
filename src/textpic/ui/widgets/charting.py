from __future__ import annotations

from datetime import date

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QDateTimeAxis,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QDateTime, QMargins, QTime, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from textpic.theme import tokens


def _font(size: int = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont("Inter")
    font.setFamilies(["Inter", "Segoe UI Variable", "Segoe UI"])
    font.setPixelSize(size)
    font.setWeight(weight)
    return font


def _chart(animate: bool = False) -> QChart:
    chart = QChart()
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(False)
    chart.setBackgroundRoundness(0)
    chart.legend().hide()
    chart.setMargins(QMargins(0, 4, 0, 0))
    if animate:
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setAnimationDuration(400)
    else:
        chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
    return chart


def _view(chart: QChart) -> QChartView:
    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    view.setStyleSheet("background: transparent; border: none;")
    view.setMinimumHeight(190)
    return view


def _style_value_axis(axis: QValueAxis) -> None:
    axis.setLabelsColor(tokens.qcolor(tokens.COLORS["TEXT_MUTED"]))
    axis.setLabelsFont(_font(10))
    axis.setLinePen(QPen(Qt.PenStyle.NoPen))
    grid_pen = QPen(tokens.qcolor(tokens.COLORS["BORDER_STRONG"], 150))
    grid_pen.setStyle(Qt.PenStyle.DashLine)
    grid_pen.setWidthF(0.8)
    axis.setGridLinePen(grid_pen)
    axis.setMinorGridLineVisible(False)
    axis.setShadesVisible(False)


def _style_category_axis(axis: QBarCategoryAxis, angle: int = 0) -> None:
    axis.setLabelsColor(tokens.qcolor(tokens.COLORS["TEXT_MUTED"]))
    axis.setLabelsFont(_font(10))
    axis.setLinePen(QPen(Qt.PenStyle.NoPen))
    axis.setGridLineVisible(False)
    axis.setLabelsAngle(angle)
    axis.setTitleText("")


def _value_max(values: list[float]) -> float:
    maximum = max(values or [0])
    if maximum <= 0:
        return 4
    return float(maximum) * 1.2


def make_bar_chart(
    categories: list[str],
    series_data: list[tuple[str, list[float], str]],
    animate: bool = False,
    angle: int = 0,
) -> QChartView:
    chart = _chart(animate)
    series = QBarSeries()
    series.setBarWidth(0.58)
    series.setLabelsVisible(False)
    all_values: list[float] = []
    for _name, values, color_token in series_data:
        bar_set = QBarSet("")
        bar_set.append([float(value) for value in values])
        bar_set.setColor(tokens.qcolor(tokens.COLORS.get(color_token, color_token)))
        bar_set.setBorderColor(Qt.GlobalColor.transparent)
        series.append(bar_set)
        all_values.extend(float(value) for value in values)
    chart.addSeries(series)

    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    _style_category_axis(axis_x, angle)
    axis_y = QValueAxis()
    axis_y.setRange(0, _value_max(all_values))
    axis_y.setTickCount(5)
    axis_y.setLabelFormat("%d")
    _style_value_axis(axis_y)
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(axis_x)
    series.attachAxis(axis_y)
    return _view(chart)


def make_donut(
    values: list[tuple[str, float]],
    animate: bool = False,
) -> QChartView:
    chart = _chart(animate)
    chart.setMargins(QMargins(4, 4, 4, 4))
    series = QPieSeries()
    series.setHoleSize(0.7)
    series.setPieSize(0.92)
    palette = tokens.CHART_COLORS
    for index, (label, value) in enumerate(values):
        if value <= 0:
            continue
        slice_item = series.append(label, float(value))
        slice_item.setBrush(
            tokens.qcolor(palette[index % len(palette)])
        )
        slice_item.setPen(QPen(Qt.PenStyle.NoPen))
        slice_item.setLabelVisible(False)
    chart.addSeries(series)
    return _view(chart)


def make_line_chart(
    dates: list[date],
    values: list[float],
    animate: bool = False,
) -> QChartView:
    chart = _chart(animate)
    series = QLineSeries()
    pen = QPen(tokens.qcolor(tokens.COLORS["ACCENT"]))
    pen.setWidthF(2.2)
    series.setPen(pen)
    for index, value in enumerate(values):
        point_date = dates[index]
        point = QDateTime(
            point_date.year,
            point_date.month,
            point_date.day,
            12,
            0,
            0,
        )
        series.append(point.toMSecsSinceEpoch(), float(value))
    chart.addSeries(series)

    if dates:
        first = QDateTime(dates[0].year, dates[0].month, dates[0].day, 0, 0, 0)
        last = QDateTime(
            dates[-1].year, dates[-1].month, dates[-1].day, 23, 59, 0
        )
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MMM d")
        axis_x.setRange(first, last)
        axis_x.setTickCount(min(7, max(2, len(dates))))
        axis_x.setLabelsColor(tokens.qcolor(tokens.COLORS["TEXT_MUTED"]))
        axis_x.setLabelsFont(_font(10))
        axis_x.setLinePen(QPen(Qt.PenStyle.NoPen))
        axis_x.setGridLineVisible(False)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

    axis_y = QValueAxis()
    axis_y.setRange(0, _value_max(values))
    axis_y.setTickCount(5)
    axis_y.setLabelFormat("%.1f")
    _style_value_axis(axis_y)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(axis_y)
    return _view(chart)


def make_hour_chart(hours: list[int], animate: bool = False) -> QChartView:
    labels = [
        f"{hour:02d}" if hour % 3 == 0 else ""
        for hour in range(24)
    ]
    return make_bar_chart(
        labels,
        [("Created", [float(value) for value in hours], "ACCENT")],
        animate=animate,
    )


def category_label(item: date, visible: bool, mode: str = "short") -> str:
    if not visible:
        return ""
    if mode == "short":
        return item.strftime("%a")
    return item.strftime("%b %d")
