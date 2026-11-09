from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from textpic.services.database import Database
from textpic.services.history_repo import (
    HistoryRepository,
    MessageFilters,
    utc_iso,
)


def make_history(tmp_path: Path) -> tuple[Database, HistoryRepository]:
    database = Database(tmp_path / "history.db")
    return database, HistoryRepository(database)


def add_message(
    history: HistoryRepository,
    text: str,
    *,
    style: str = "sent_blue",
    days_ago: int = 0,
    pinned: bool = False,
    status: str = "rendered",
    image: str | None = None,
):
    created = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return history.add(
        text=text,
        style_key=style,
        theme="light",
        font="Segoe UI",
        font_size=15,
        scale=2,
        image_path=image,
        status=status,
        created_utc=utc_iso(created),
        pinned=pinned,
    )


def test_filters_and_counts(tmp_path: Path) -> None:
    database, history = make_history(tmp_path)
    try:
        add_message(history, "Hello Maya", style="sent_blue", days_ago=0)
        add_message(
            history,
            "Price quote",
            style="received_dark",
            days_ago=3,
            status="pasted",
        )
        add_message(
            history,
            "Pinned note",
            style="plain_dark",
            days_ago=120,
            pinned=True,
        )
        assert history.count() == 3
        assert history.count(MessageFilters(search="maya")) == 1
        assert history.count(MessageFilters(style_key="received_dark")) == 1
        assert history.count(MessageFilters(status="pasted")) == 1
        assert history.count(MessageFilters(pinned_only=True)) == 1
        assert history.count(MessageFilters(date_from=datetime.now().date())) == 1
        grouped = history.all_filtered(MessageFilters(search="o"))
        assert any(record.text == "Hello Maya" for record in grouped)
    finally:
        database.close()


def test_retention_keeps_pinned_rows(tmp_path: Path) -> None:
    database, history = make_history(tmp_path)
    try:
        old = add_message(history, "Old", days_ago=400, image="old.png")
        keep = add_message(
            history,
            "Pinned",
            days_ago=400,
            pinned=True,
            image="pinned.png",
        )
        recent = add_message(history, "Recent", days_ago=1, image="recent.png")
        paths = history.delete_older_than(90)
        assert "old.png" in paths
        assert history.get(old.id) is None
        assert history.get(keep.id) is not None
        assert history.get(recent.id) is not None
    finally:
        database.close()


def test_mark_pasted_and_pin(tmp_path: Path) -> None:
    database, history = make_history(tmp_path)
    try:
        record = add_message(history, "Hello")
        history.mark_pasted(record.id)
        updated = history.get(record.id)
        assert updated is not None
        assert updated.status == "pasted"
        assert updated.pasted_utc
        history.set_pinned(record.id, True)
        assert history.get(record.id).pinned
    finally:
        database.close()
