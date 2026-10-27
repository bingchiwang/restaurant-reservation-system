from backend.app.utils.db import get_db_cursor

class UserDAO:
    def __init__(self, conn):
        self.conn = conn

    def get_by_email(self, email: str):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT user_id, email, password_hash, display_name, role, status, created_at, updated_at
                FROM users
                WHERE email = ?
            """, (email.strip().lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_id(self, user_id: int):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT user_id, email, password_hash, display_name, role, status, created_at, updated_at
                FROM users
                WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_user(self, email: str, password_hash: str, display_name: str, role: str = "MEMBER", status: str = "ACTIVE"):
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                INSERT INTO users (email, password_hash, display_name, role, status)
                VALUES (?, ?, ?, ?, ?)
            """, (email.strip().lower(), password_hash, display_name, role, status))
            return cursor.lastrowid
