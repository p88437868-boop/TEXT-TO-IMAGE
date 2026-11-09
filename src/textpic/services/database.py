from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable


MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_utc TEXT NOT NULL,
            text TEXT NOT NULL,
            style_key TEXT NOT NULL,
            theme TEXT NOT NULL,
            font TEXT NOT NULL,
            font_size INTEGER NOT NULL,
            scale REAL NOT NULL,
            chars INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'rendered',
            pasted_utc TEXT NULL,
            pinned INTEGER NOT NULL DEFAULT 0,
            image_path TEXT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_utc);
        CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
        CREATE INDEX IF NOT EXISTS idx_messages_pinned ON messages(pinned);

        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            hotkey TEXT NULL,
            created_utc TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """,
    )
]


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self) -> None:
        current = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
        for version, script in MIGRATIONS:
            if version > current:
                with self.connection:
                    self.connection.executescript(script)
                    self.connection.execute(f"PRAGMA user_version={version}")
                current = version

    def execute(self, sql: str, parameters: Iterable[Any] = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, tuple(parameters))

    def executemany(
        self, sql: str, rows: Iterable[Iterable[Any]]
    ) -> sqlite3.Cursor:
        return self.connection.executemany(sql, rows)

    def commit(self) -> None:
        self.connection.commit()

    def query(self, sql: str, parameters: Iterable[Any] = ()) -> list[sqlite3.Row]:
        return list(self.connection.execute(sql, tuple(parameters)).fetchall())

    def query_one(
        self, sql: str, parameters: Iterable[Any] = ()
    ) -> sqlite3.Row | None:
        return self.connection.execute(sql, tuple(parameters)).fetchone()

    def close(self) -> None:
        try:
            self.connection.commit()
        finally:
            self.connection.close()
