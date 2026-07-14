import os
import sqlite3
import secrets
import time
from contextlib import contextmanager
from typing import List, Dict, Optional
import bcrypt
import logging

logger = logging.getLogger(__name__)

SESSION_TTL = 60 * 60 * 24 * 7  # 7 days in seconds


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lexassist.db")
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    category TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    query_id INTEGER NOT NULL,
                    note TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, query_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (query_id) REFERENCES query_history(id)
                );
                -- migrate: add note column if missing
                CREATE TEMPORARY TABLE IF NOT EXISTS _dummy_bookmarks_note AS
                    SELECT 1 WHERE 0;

                CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
                CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
                CREATE INDEX IF NOT EXISTS idx_history_user ON query_history(user_id);
                CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id);
            """)
        logger.info("Database initialized")
        self._migrate()

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _check_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def register_user(self, username: str, password: str) -> bool:
        try:
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, self._hash_password(password))
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username: str, password: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            if row and self._check_password(password, dict(row)["password_hash"]):
                return dict(row)
        return None

    # ── Session management ────────────────────────────────────────────────

    def create_session(self, user_id: int) -> str:
        token = secrets.token_hex(32)
        expires_at = int(time.time()) + SESSION_TTL
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
                (token, user_id, expires_at)
            )
        return token

    def get_session_user(self, token: str) -> Optional[int]:
        """Returns user_id if token is valid and not expired, else None."""
        now = int(time.time())
        with self._conn() as conn:
            row = conn.execute(
                "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
                (token, now)
            ).fetchone()
        return row["user_id"] if row else None

    def delete_session(self, token: str):
        with self._conn() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))

    def purge_expired_sessions(self):
        with self._conn() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (int(time.time()),))

    # ── Query history ─────────────────────────────────────────────────────

    def save_query(self, query: str, response: str, category: str, user_id: int = None) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO query_history (user_id, query, response, category) VALUES (?, ?, ?, ?)",
                (user_id, query, response, category)
            )
            return cursor.lastrowid

    def get_history(self, limit: int = 10, offset: int = 0, user_id: int = None, search: str = None) -> List[Dict]:
        with self._conn() as conn:
            conditions = []
            params = []
            if user_id is not None:
                conditions.append("user_id = ?")
                params.append(int(user_id))
            if search:
                conditions.append("query LIKE ?")
                params.append(f"%{search}%")
            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            rows = conn.execute(
                f"SELECT * FROM query_history {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (*params, limit, offset)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_history_count(self, user_id: int = None, search: str = None) -> int:
        with self._conn() as conn:
            conditions = []
            params = []
            if user_id is not None:
                conditions.append("user_id = ?")
                params.append(int(user_id))
            if search:
                conditions.append("query LIKE ?")
                params.append(f"%{search}%")
            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            row = conn.execute(
                f"SELECT COUNT(*) FROM query_history {where}", params
            ).fetchone()
        return row[0]

    # ── Bookmarks ─────────────────────────────────────────────────────────

    def _migrate(self):
        """Add columns introduced after initial schema creation."""
        with self._conn() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(bookmarks)").fetchall()]
            if "note" not in cols:
                conn.execute("ALTER TABLE bookmarks ADD COLUMN note TEXT DEFAULT ''")

    def toggle_bookmark(self, user_id: int, query_id: int) -> bool:
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT id FROM bookmarks WHERE user_id = ? AND query_id = ?",
                (user_id, query_id)
            ).fetchone()
            if existing:
                conn.execute(
                    "DELETE FROM bookmarks WHERE user_id = ? AND query_id = ?",
                    (user_id, query_id)
                )
                return False
            conn.execute(
                "INSERT INTO bookmarks (user_id, query_id) VALUES (?, ?)",
                (user_id, query_id)
            )
            return True

    def update_bookmark_note(self, user_id: int, query_id: int, note: str) -> bool:
        with self._conn() as conn:
            cursor = conn.execute(
                "UPDATE bookmarks SET note = ? WHERE user_id = ? AND query_id = ?",
                (note[:500], user_id, query_id)
            )
        return cursor.rowcount > 0

    def get_bookmarks(self, user_id: int) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT qh.*, 1 as bookmarked, b.note as bookmark_note
                FROM query_history qh
                INNER JOIN bookmarks b ON b.query_id = qh.id
                WHERE b.user_id = ?
                ORDER BY b.created_at DESC
            """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def delete_history_entry(self, entry_id: int, user_id: int) -> bool:
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM query_history WHERE id = ? AND user_id = ?",
                (entry_id, user_id)
            )
        return cursor.rowcount > 0

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if not row or not self._check_password(old_password, row["password_hash"]):
                return False
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (self._hash_password(new_password), user_id)
            )
        return True

    def get_bookmarked_ids(self, user_id: int) -> set:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT query_id FROM bookmarks WHERE user_id = ?", (user_id,)
            ).fetchall()
        return {r[0] for r in rows}

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM query_history").fetchone()[0]
            by_cat = dict(conn.execute(
                "SELECT category, COUNT(*) FROM query_history GROUP BY category"
            ).fetchall())
        return {"total_queries": total, "by_category": by_cat}

    def get_user_stats(self, user_id: int) -> Dict:
        with self._conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM query_history WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            by_cat = dict(conn.execute(
                "SELECT category, COUNT(*) FROM query_history WHERE user_id = ? GROUP BY category",
                (user_id,)
            ).fetchall())
            by_day = dict(conn.execute(
                "SELECT DATE(timestamp) as day, COUNT(*) FROM query_history WHERE user_id = ? GROUP BY day ORDER BY day DESC LIMIT 30",
                (user_id,)
            ).fetchall())
            most_active = max(by_day, key=by_day.get) if by_day else None
            bookmarks_count = conn.execute(
                "SELECT COUNT(*) FROM bookmarks WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
        return {
            "total_queries": total,
            "by_category": by_cat,
            "by_day": by_day,
            "most_active_day": most_active,
            "bookmarks_count": bookmarks_count,
        }
