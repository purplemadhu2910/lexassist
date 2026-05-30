import os
import sqlite3
from typing import List, Dict
import bcrypt
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join("/tmp", "lexassist.db")
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                category TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized")

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _check_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def register_user(self, username: str, password: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, self._hash_password(password))
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def login_user(self, username: str, password: str) -> Dict | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row and self._check_password(password, dict(row)["password_hash"]):
                return dict(row)
            return None
        finally:
            conn.close()

    def save_query(self, query: str, response: str, category: str, user_id: int = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO query_history (user_id, query, response, category) VALUES (?, ?, ?, ?)",
            (user_id, query, response, category)
        )
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return query_id

    def get_history(self, limit: int = 50, user_id: int = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if user_id is not None:
            cursor.execute(
                "SELECT * FROM query_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (int(user_id), limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM query_history ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM query_history")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT category, COUNT(*) FROM query_history GROUP BY category")
        by_category = dict(cursor.fetchall())

        conn.close()
        return {"total_queries": total, "by_category": by_category}
