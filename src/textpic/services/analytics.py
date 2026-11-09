from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from textpic.services.database import Database
from textpic.services.history_repo import parse_utc, utc_now
from textpic.theme.tokens import STYLE_LABELS


def _utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _local_range_utc(start: date, end: date) -> tuple[str, str]:
    start_local = datetime.combine(start, time.min).astimezone()
    end_local = datetime.combine(end + timedelta(days=1), time.min).astimezone()
    return _utc_iso(start_local), _utc_iso(end_local)


def _trend(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100.0, 1)


class AnalyticsService:
    def __init__(self, database: Database):
        self.database = database

    def _count_created(self, start_iso: str, end_iso: str) -> int:
        row = self.database.query_one(
            """
            SELECT COUNT(*) AS total FROM messages
            WHERE created_utc >= ? AND created_utc < ?
            """,
            (start_iso, end_iso),
        )
        return int(row["total"]) if row else 0

    def _count_pasted(self, start_iso: str, end_iso: str) -> int:
        row = self.database.query_one(
            """
            SELECT COUNT(*) AS total FROM messages
            WHERE pasted_utc IS NOT NULL AND pasted_utc >= ? AND pasted_utc < ?
            """,
            (start_iso, end_iso),
        )
        return int(row["total"]) if row else 0

    def _avg_length(self, start_iso: str, end_iso: str) -> float:
        row = self.database.query_one(
            """
            SELECT AVG(chars) AS average FROM messages
            WHERE created_utc >= ? AND created_utc < ?
            """,
            (start_iso, end_iso),
        )
        return float(row["average"] or 0) if row else 0.0

    def overview(self, days: int = 7) -> dict[str, Any]:
        now = utc_now()
        current_start = now - timedelta(days=days)
        previous_start = now - timedelta(days=days * 2)
        current_start_iso = _utc_iso(current_start)
        previous_start_iso = _utc_iso(previous_start)
        now_iso = _utc_iso(now)

        created = self._count_created(current_start_iso, now_iso)
        created_previous = self._count_created(previous_start_iso, current_start_iso)
        pasted = self._count_pasted(current_start_iso, now_iso)
        pasted_previous = self._count_pasted(previous_start_iso, current_start_iso)
        average = self._avg_length(current_start_iso, now_iso)
        average_previous = self._avg_length(previous_start_iso, current_start_iso)

        local_today = date.today()
        local_tomorrow = local_today + timedelta(days=1)
        today_start_iso, today_end_iso = _local_range_utc(
            local_today, local_tomorrow - timedelta(days=1)
        )
        yesterday_start_iso, yesterday_end_iso = _local_range_utc(
            local_today - timedelta(days=1), local_today - timedelta(days=1)
        )
        today_created = self._count_created(today_start_iso, today_end_iso)
        today_pasted = self._count_pasted(today_start_iso, today_end_iso)
        yesterday_created = self._count_created(yesterday_start_iso, yesterday_end_iso)
        average_today = self._avg_length(today_start_iso, today_end_iso)

        return {
            "created": created,
            "created_trend": _trend(created, created_previous),
            "created_today": today_created,
            "pasted": pasted,
            "pasted_trend": _trend(pasted, pasted_previous),
            "pasted_today": today_pasted,
            "today": today_created,
            "today_trend": _trend(today_created, yesterday_created),
            "today_pasted": today_pasted,
            "average_length": round(average, 1),
            "average_trend": _trend(average, average_previous),
            "average_today": round(average_today, 1),
            "period_days": days,
        }

    def daily_activity(self, days: int = 7) -> dict[str, Any]:
        today = date.today()
        start = today - timedelta(days=days - 1)
        start_iso, end_iso = _local_range_utc(start, today)
        created_rows = self.database.query(
            """
            SELECT created_utc FROM messages
            WHERE created_utc >= ? AND created_utc < ?
            """,
            (start_iso, end_iso),
        )
        pasted_rows = self.database.query(
            """
            SELECT pasted_utc FROM messages
            WHERE pasted_utc IS NOT NULL AND pasted_utc >= ? AND pasted_utc < ?
            """,
            (start_iso, end_iso),
        )
        created_counter: Counter[date] = Counter()
        pasted_counter: Counter[date] = Counter()
        for row in created_rows:
            parsed = parse_utc(row["created_utc"])
            if parsed:
                created_counter[parsed.astimezone().date()] += 1
        for row in pasted_rows:
            parsed = parse_utc(row["pasted_utc"])
            if parsed:
                pasted_counter[parsed.astimezone().date()] += 1
        days_list = [start + timedelta(days=index) for index in range(days)]
        return {
            "dates": days_list,
            "created": [created_counter[item] for item in days_list],
            "pasted": [pasted_counter[item] for item in days_list],
        }

    def style_usage(self, days: int = 30) -> list[dict[str, Any]]:
        today = date.today()
        start = today - timedelta(days=days - 1)
        start_iso, end_iso = _local_range_utc(start, today)
        rows = self.database.query(
            """
            SELECT style_key, COUNT(*) AS total FROM messages
            WHERE created_utc >= ? AND created_utc < ?
            GROUP BY style_key ORDER BY total DESC
            """,
            (start_iso, end_iso),
        )
        return [
            {
                "style_key": row["style_key"],
                "label": STYLE_LABELS.get(row["style_key"], row["style_key"]),
                "count": int(row["total"]),
            }
            for row in rows
        ]

    def snapshot(self, start: date, end: date) -> dict[str, Any]:
        start_iso, end_iso = _local_range_utc(start, end)
        created_rows = self.database.query(
            """
            SELECT created_utc, chars, style_key FROM messages
            WHERE created_utc >= ? AND created_utc < ?
            """,
            (start_iso, end_iso),
        )
        pasted_rows = self.database.query(
            """
            SELECT pasted_utc FROM messages
            WHERE pasted_utc IS NOT NULL AND pasted_utc >= ? AND pasted_utc < ?
            """,
            (start_iso, end_iso),
        )
        day_count = (end - start).days + 1
        days = [start + timedelta(days=index) for index in range(day_count)]
        created_by_day: Counter[date] = Counter()
        pasted_by_day: Counter[date] = Counter()
        style_counts: Counter[str] = Counter()
        hour_counts: Counter[int] = Counter()
        length_by_day: dict[date, list[int]] = {item: [] for item in days}
        for row in created_rows:
            parsed = parse_utc(row["created_utc"])
            if not parsed:
                continue
            local = parsed.astimezone()
            created_by_day[local.date()] += 1
            style_counts[row["style_key"]] += 1
            hour_counts[local.hour] += 1
            if local.date() in length_by_day:
                length_by_day[local.date()].append(int(row["chars"]))
        for row in pasted_rows:
            parsed = parse_utc(row["pasted_utc"])
            if parsed:
                local_date = parsed.astimezone().date()
                if start <= local_date <= end:
                    pasted_by_day[local_date] += 1
        average_by_day = [
            (sum(length_by_day[item]) / len(length_by_day[item]))
            if length_by_day[item]
            else 0.0
            for item in days
        ]
        styles = sorted(style_counts.items(), key=lambda item: (-item[1], item[0]))
        return {
            "start": start,
            "end": end,
            "days": days,
            "created": [created_by_day[item] for item in days],
            "pasted": [pasted_by_day[item] for item in days],
            "styles": [
                {
                    "style_key": key,
                    "label": STYLE_LABELS.get(key, key),
                    "count": count,
                }
                for key, count in styles
            ],
            "hours": [hour_counts[hour] for hour in range(24)],
            "average_length": average_by_day,
            "total_created": len(created_rows),
            "total_pasted": sum(pasted_by_day.values()),
            "total_chars": sum(int(row["chars"]) for row in created_rows),
        }
