from backend.app.utils.db import get_db_cursor

class UserDAO:
    def __init__(self, conn):
        self.conn = conn

    def get_by_email(self, email: str):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT user_id, email, password_hash, display_name, phone, gender, birthday, role, status, created_at, updated_at
                FROM users
                WHERE email = ?
            """, (email.strip().lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_id(self, user_id: int):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT user_id, email, password_hash, display_name, phone, gender, birthday, role, status, created_at, updated_at
                FROM users
                WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_user(
        self,
        email: str,
        password_hash: str,
        display_name: str,
        phone: str = None,
        gender: str = None,
        birthday: str = None,
        role: str = "MEMBER",
        status: str = "ACTIVE",
    ):
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                INSERT INTO users (email, password_hash, display_name, phone, gender, birthday, role, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (email.strip().lower(), password_hash, display_name, phone, gender, birthday, role, status))
            return cursor.lastrowid

    def update_user(self, user_id: int, fields: dict):
        """Updates allowed user profile fields (display_name, phone, gender, birthday, password_hash)."""
        allowed = {"display_name", "phone", "gender", "birthday", "password_hash"}
        update_cols = []
        params = []
        for k, v in fields.items():
            if k in allowed:
                update_cols.append(f"{k} = ?")
                params.append(v)
        if not update_cols:
            return False
        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(update_cols)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute(sql, tuple(params))
            return cursor.rowcount > 0
