"""SQLite storage for sales. Each chat keeps its own records."""

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = """
CREATE TABLE IF NOT EXISTS sales (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    INTEGER NOT NULL,
    amount     REAL    NOT NULL,
    note       TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL  -- ISO time in the shop's timezone
);
CREATE INDEX IF NOT EXISTS idx_sales_chat_time ON sales (chat_id, created_at);
"""


@dataclass(frozen=True)
class Sale:
    id: int
    amount: float
    note: str
    created_at: datetime


class SalesDB:
    def __init__(self, path: Path, tz: ZoneInfo):
        self.tz = tz
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)

    def now(self) -> datetime:
        return datetime.now(self.tz).replace(microsecond=0)

    def add(self, chat_id: int, amount: float, note: str) -> Sale:
        created = self.now()
        cur = self.conn.execute(
            "INSERT INTO sales (chat_id, amount, note, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, amount, note, created.isoformat()),
        )
        self.conn.commit()
        return Sale(cur.lastrowid, amount, note, created)

    def undo_last(self, chat_id: int) -> Sale | None:
        row = self.conn.execute(
            "SELECT id, amount, note, created_at FROM sales WHERE chat_id = ? ORDER BY id DESC LIMIT 1",
            (chat_id,),
        ).fetchone()
        if row is None:
            return None
        self.conn.execute("DELETE FROM sales WHERE id = ?", (row[0],))
        self.conn.commit()
        return self._sale(row)

    def between(self, chat_id: int, start: date, end: date) -> list[Sale]:
        """Sales from the start day to the end day, both inclusive."""
        rows = self.conn.execute(
            "SELECT id, amount, note, created_at FROM sales "
            "WHERE chat_id = ? AND created_at >= ? AND created_at < ? ORDER BY created_at",
            (chat_id, start.isoformat(), (end + timedelta(days=1)).isoformat()),
        ).fetchall()
        return [self._sale(r) for r in rows]

    def all(self, chat_id: int) -> list[Sale]:
        rows = self.conn.execute(
            "SELECT id, amount, note, created_at FROM sales WHERE chat_id = ? ORDER BY created_at",
            (chat_id,),
        ).fetchall()
        return [self._sale(r) for r in rows]

    @staticmethod
    def _sale(row) -> Sale:
        return Sale(row[0], row[1], row[2], datetime.fromisoformat(row[3]))
