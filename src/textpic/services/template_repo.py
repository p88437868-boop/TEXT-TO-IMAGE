from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textpic.services.database import Database
from textpic.services.history_repo import utc_iso


SAMPLE_TEMPLATES = [
    (
        "Friendly greeting",
        "Hi {name}! Thanks for reaching out 😊 How can I help today?",
        "Ctrl+Alt+1",
    ),
    (
        "Price quote",
        "Hi {name}, the {product} is {price}. It includes delivery and a 1-year warranty.",
        "Ctrl+Alt+2",
    ),
    (
        "Still interested?",
        "Hi {name}, just checking in — are you still interested in the {product}?",
        "Ctrl+Alt+3",
    ),
    (
        "Delivery information",
        "Hi {name}, delivery usually takes 3–5 business days. I’ll send tracking as soon as it ships.",
        "Ctrl+Alt+4",
    ),
    (
        "Thank you",
        "Thank you so much, {name}! I’m glad I could help. Let me know if you need anything else.",
        "Ctrl+Alt+5",
    ),
    (
        "Follow-up",
        "Hi {name}, I wanted to follow up on the {product}. Would you like me to reserve one for you?",
        "Ctrl+Alt+6",
    ),
]


@dataclass
class TemplateRecord:
    id: int
    title: str
    body: str
    hotkey: str | None
    created_utc: str

    @classmethod
    def from_row(cls, row: Any) -> "TemplateRecord":
        return cls(
            id=int(row["id"]),
            title=row["title"],
            body=row["body"],
            hotkey=row["hotkey"],
            created_utc=row["created_utc"],
        )


class TemplateRepository:
    def __init__(self, database: Database):
        self.database = database

    def seed_defaults(self, force: bool = False) -> None:
        count = int(
            self.database.query_one("SELECT COUNT(*) AS total FROM templates")["total"]
        )
        if count and not force:
            return
        if force:
            with self.database.connection:
                self.database.execute("DELETE FROM templates")
        with self.database.connection:
            for title, body, hotkey in SAMPLE_TEMPLATES:
                self.database.execute(
                    """
                    INSERT INTO templates(title, body, hotkey, created_utc)
                    VALUES(?, ?, ?, ?)
                    """,
                    (title, body, hotkey, utc_iso()),
                )

    def list_all(self) -> list[TemplateRecord]:
        rows = self.database.query(
            "SELECT * FROM templates ORDER BY id ASC"
        )
        return [TemplateRecord.from_row(row) for row in rows]

    def get(self, template_id: int) -> TemplateRecord | None:
        row = self.database.query_one(
            "SELECT * FROM templates WHERE id = ?", (template_id,)
        )
        return TemplateRecord.from_row(row) if row else None

    def _assert_hotkey_free(
        self, hotkey: str | None, ignore_id: int | None = None
    ) -> None:
        if not hotkey:
            return
        row = self.database.query_one(
            "SELECT id FROM templates WHERE hotkey = ? AND id != ?",
            (hotkey, ignore_id or -1),
        )
        if row:
            raise ValueError(f"Hotkey {hotkey} is already assigned to another template.")

    def create(self, title: str, body: str, hotkey: str | None) -> TemplateRecord:
        if not title.strip():
            raise ValueError("A template title is required.")
        if not body.strip():
            raise ValueError("A template message is required.")
        self._assert_hotkey_free(hotkey)
        with self.database.connection:
            cursor = self.database.execute(
                """
                INSERT INTO templates(title, body, hotkey, created_utc)
                VALUES(?, ?, ?, ?)
                """,
                (title.strip(), body, hotkey or None, utc_iso()),
            )
        record = self.get(int(cursor.lastrowid))
        if record is None:
            raise RuntimeError("Could not read the new template.")
        return record

    def update(
        self, template_id: int, title: str, body: str, hotkey: str | None
    ) -> TemplateRecord:
        if not title.strip():
            raise ValueError("A template title is required.")
        if not body.strip():
            raise ValueError("A template message is required.")
        self._assert_hotkey_free(hotkey, template_id)
        with self.database.connection:
            self.database.execute(
                """
                UPDATE templates SET title = ?, body = ?, hotkey = ? WHERE id = ?
                """,
                (title.strip(), body, hotkey or None, template_id),
            )
        record = self.get(template_id)
        if record is None:
            raise RuntimeError("Template no longer exists.")
        return record

    def delete(self, template_id: int) -> None:
        with self.database.connection:
            self.database.execute(
                "DELETE FROM templates WHERE id = ?", (template_id,)
            )

    def count(self) -> int:
        row = self.database.query_one("SELECT COUNT(*) AS total FROM templates")
        return int(row["total"]) if row else 0
