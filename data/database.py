import os
import sqlite3
from contextlib import closing
from datetime import datetime


class DatabaseHandler:
    def __init__(self, db_path="data/db.sqlite"):
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with closing(self._connect()) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL UNIQUE,
                    filepath TEXT,
                    thumbnail_path TEXT,
                    subreddit TEXT NOT NULL,
                    duration REAL NOT NULL,
                    url TEXT NOT NULL,
                    has_audio INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    posted_to_instagram INTEGER DEFAULT 0,
                    instagram_post_id TEXT,
                    instagram_posted_at TEXT
                )
                """
            )
            conn.commit()

    def add_video(self, metadata):
        try:
            created_at = (
                metadata.get("timestamp")
                or metadata.get("created_at")
                or datetime.now().isoformat()
            )
            with closing(self._connect()) as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO videos
                    (title, filename, filepath, thumbnail_path, subreddit, duration, url, has_audio, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        metadata["title"],
                        metadata["filename"],
                        metadata.get("filepath", ""),
                        metadata.get("thumbnail_path", ""),
                        metadata["subreddit"],
                        metadata["duration"],
                        metadata["url"],
                        1 if metadata.get("has_audio") else 0,
                        created_at,
                    ),
                )
                conn.commit()
                return conn.total_changes > 0
        except (KeyError, TypeError, sqlite3.Error):
            return False

    save_video = add_video

    def is_duplicate(self, filename):
        if not filename:
            return False
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT 1 FROM videos WHERE filename = ?",
                (filename,),
            ).fetchone()
            return row is not None

    def get_all_videos(self):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM videos ORDER BY created_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def get_recent(self, limit):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM videos ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def mark_posted(self, filename, post_id):
        posted_at = datetime.now().isoformat()
        with closing(self._connect()) as conn:
            conn.execute(
                """
                UPDATE videos
                SET posted_to_instagram = 1,
                    instagram_post_id = ?,
                    instagram_posted_at = ?
                WHERE filename = ?
                """,
                (post_id, posted_at, filename),
            )
            conn.commit()
            return conn.total_changes > 0

    def get_posts_today(self):
        today = datetime.now().date().isoformat()
        with closing(self._connect()) as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM videos
                WHERE posted_to_instagram = 1
                  AND substr(instagram_posted_at, 1, 10) = ?
                """,
                (today,),
            ).fetchone()
            return int(row["count"])
