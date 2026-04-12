"""SQLite database for lesson progress persistence.

The database is created lazily on first access and stored at ``db/progress.db``
relative to the project root.
"""

from __future__ import annotations

import os
from pathlib import Path

import aiosqlite

_DB_DIR = Path(
    os.environ.get(
        "PIANO_DB_DIR", Path(__file__).resolve().parent.parent.parent / "db"
    )
)
_DB_PATH = _DB_DIR / "progress.db"

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS lesson_progress (
    lesson_id   TEXT PRIMARY KEY,
    best_score  REAL NOT NULL DEFAULT 0.0,
    attempts    INTEGER NOT NULL DEFAULT 0,
    completed   INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


async def _get_db() -> aiosqlite.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(_DB_PATH))
    await db.executescript(_SCHEMA)
    return db


async def get_progress(lesson_id: str) -> dict | None:
    """Return progress dict for a lesson, or None if never attempted."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT lesson_id, best_score, attempts, completed FROM lesson_progress WHERE lesson_id = ?",
            (lesson_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "lesson_id": row[0],
            "best_score": row[1],
            "attempts": row[2],
            "completed": bool(row[3]),
        }
    finally:
        await db.close()


async def get_all_progress() -> dict[str, dict]:
    """Return {lesson_id: progress_dict} for all lessons with progress."""
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT lesson_id, best_score, attempts, completed FROM lesson_progress"
        )
        rows = await cursor.fetchall()
        return {
            row[0]: {
                "lesson_id": row[0],
                "best_score": row[1],
                "attempts": row[2],
                "completed": bool(row[3]),
            }
            for row in rows
        }
    finally:
        await db.close()


async def save_attempt(lesson_id: str, score: float, passed: bool) -> None:
    """Record a lesson attempt. Updates best_score if this is higher."""
    db = await _get_db()
    try:
        await db.execute(
            """\
            INSERT INTO lesson_progress (lesson_id, best_score, attempts, completed, updated_at)
            VALUES (?, ?, 1, ?, datetime('now'))
            ON CONFLICT(lesson_id) DO UPDATE SET
                best_score = MAX(lesson_progress.best_score, excluded.best_score),
                attempts = lesson_progress.attempts + 1,
                completed = MAX(lesson_progress.completed, excluded.completed),
                updated_at = datetime('now')
            """,
            (lesson_id, score, int(passed)),
        )
        await db.commit()
    finally:
        await db.close()


async def reset_progress() -> None:
    """Clear all progress (for testing)."""
    db = await _get_db()
    try:
        await db.execute("DELETE FROM lesson_progress")
        await db.commit()
    finally:
        await db.close()
