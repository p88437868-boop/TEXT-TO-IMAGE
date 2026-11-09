from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from textpic.services.database import Database


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso(value: datetime | None = None) -> str:
    return (value or utc_now()).astimezone(timezone.utc).isoformat()


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def local_display(value: str | None) -> str:
    parsed = parse_utc(value)
    if parsed is None:
        return ""
    return parsed.astimezone().strftime("%b %d, %H:%M")


def local_date(value: str | None) -> date | None:
    parsed = parse_utc(value)
    return parsed.astimezone().date() if parsed else None


def _day_start_utc(day: date) -> str:
    local = datetime.combine(day, time.min).astimezone()
    return local.astimezone(timezone.utc).isoformat()


@dataclass
class MessageRecord:
    id: int
    created_utc: str
    text: str
    style_key: str
    theme: str
    font: str
    font_size: int
    scale: float
    chars: int
    status: str
    pasted_utc: str | None
    pinned: bool
    image_path: str | None

    @classmethod
    def from_row(cls, row: Any) -> "MessageRecord":
        return cls(
            id=int(row["id"]),
            created_utc=row["created_utc"],
            text=row["text"],
            style_key=row["style_key"],
            theme=row["theme"],
            font=row["font"],
            font_size=int(row["font_size"]),
            scale=float(row["scale"]),
            chars=int(row["chars"]),
            status=row["status"],
            pasted_utc=row["pasted_utc"],
            pinned=bool(row["pinned"]),
            image_path=row["image_path"],
        )

    @property
    def preview(self) -> str:
        text = " ".join(self.text.split())
        return text[:96] + ("…" if len(text) > 96 else "")

    @property
    def local_time(self) -> str:
        return local_display(self.created_utc)


@dataclass
class MessageFilters:
    search: str = ""
    date_from: date | None = None
    date_to: date | None = None
    pinned_only: bool = False
    status: str = ""
    style_key: str = ""

    def where(self) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if self.search.strip():
            clauses.append("(text LIKE ? OR style_key LIKE ?)")
            term = f"%{self.search.strip()}%"
            params.extend([term, term])
        if self.date_from:
            clauses.append("created_utc >= ?")
            params.append(_day_start_utc(self.date_from))
        if self.date_to:
            clauses.append("created_utc < ?")
            params.append(_day_start_utc(self.date_to + timedelta(days=1)))
        if self.pinned_only:
            clauses.append("pinned = 1")
        if self.status:
            clauses.append("status = ?")
            params.append(self.status)
        if self.style_key:
            clauses.append("style_key = ?")
            params.append(self.style_key)
        if not clauses:
            return "", params
        return " WHERE " + " AND ".join(clauses), params


class HistoryRepository:
    def __init__(self, database: Database):
        self.database = database

    def add(
        self,
        *,
        text: str,
        style_key: str,
        theme: str,
        font: str,
        font_size: int,
        scale: float,
        image_path: str | None,
        status: str = "rendered",
        created_utc: str | None = None,
        pasted_utc: str | None = None,
        pinned: bool = False,
    ) -> MessageRecord:
        created = created_utc or utc_iso()
        with self.database.connection:
            cursor = self.database.execute(
                """
                INSERT INTO messages(
                    created_utc, text, style_key, theme, font, font_size, scale,
                    chars, status, pasted_utc, pinned, image_path
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created,
                    text,
                    style_key,
                    theme,
                    font,
                    font_size,
                    scale,
                    len(text),
                    status,
                    pasted_utc,
                    1 if pinned else 0,
                    image_path,
                ),
            )
        record = self.get(int(cursor.lastrowid))
        if record is None:
            raise RuntimeError("Could not read the newly created message.")
        return record

    def get(self, message_id: int) -> MessageRecord | None:
        row = self.database.query_one(
            "SELECT * FROM messages WHERE id = ?", (message_id,)
        )
        return MessageRecord.from_row(row) if row else None

    def count(self, filters: MessageFilters | None = None) -> int:
        filters = filters or MessageFilters()
        where, params = filters.where()
        row = self.database.query_one(
            f"SELECT COUNT(*) AS total FROM messages{where}", params
        )
        return int(row["total"]) if row else 0

    def fetch(
        self,
        offset: int,
        limit: int,
        filters: MessageFilters | None = None,
        newest_first: bool = True,
    ) -> list[MessageRecord]:
        filters = filters or MessageFilters()
        where, params = filters.where()
        order = "DESC" if newest_first else "ASC"
        rows = self.database.query(
            f"""
            SELECT * FROM messages{where}
            ORDER BY created_utc {order}, id {order}
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        )
        return [MessageRecord.from_row(row) for row in rows]

    def all_filtered(self, filters: MessageFilters) -> list[MessageRecord]:
        where, params = filters.where()
        rows = self.database.query(
            f"SELECT * FROM messages{where} ORDER BY created_utc DESC, id DESC",
            params,
        )
        return [MessageRecord.from_row(row) for row in rows]

    def recent(self, limit: int = 10) -> list[MessageRecord]:
        rows = self.database.query(
            "SELECT * FROM messages ORDER BY created_utc DESC, id DESC LIMIT ?",
            (limit,),
        )
        return [MessageRecord.from_row(row) for row in rows]

    def mark_pasted(self, message_id: int, when: str | None = None) -> None:
        with self.database.connection:
            self.database.execute(
                """
                UPDATE messages SET status = 'pasted', pasted_utc = ? WHERE id = ?
                """,
                (when or utc_iso(), message_id),
            )

    def set_pinned(self, message_id: int, pinned: bool) -> None:
        with self.database.connection:
            self.database.execute(
                "UPDATE messages SET pinned = ? WHERE id = ?",
                (1 if pinned else 0, message_id),
            )

    def delete_ids(self, ids: list[int]) -> list[str]:
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        rows = self.database.query(
            f"SELECT image_path FROM messages WHERE id IN ({placeholders})", ids
        )
        paths = [str(row["image_path"]) for row in rows if row["image_path"]]
        with self.database.connection:
            self.database.execute(
                f"DELETE FROM messages WHERE id IN ({placeholders})", ids
            )
        return paths

    def delete_older_than(self, days: int) -> list[str]:
        if days <= 0:
            return []
        cutoff = utc_iso(utc_now() - timedelta(days=days))
        rows = self.database.query(
            """
            SELECT image_path FROM messages
            WHERE created_utc < ? AND pinned = 0
            """,
            (cutoff,),
        )
        paths = [str(row["image_path"]) for row in rows if row["image_path"]]
        with self.database.connection:
            self.database.execute(
                "DELETE FROM messages WHERE created_utc < ? AND pinned = 0",
                (cutoff,),
            )
        return paths

    def clear(self) -> list[str]:
        rows = self.database.query(
            "SELECT image_path FROM messages WHERE image_path IS NOT NULL"
        )
        paths = [str(row["image_path"]) for row in rows]
        with self.database.connection:
            self.database.execute("DELETE FROM messages")
        return paths
