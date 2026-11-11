from datetime import datetime
from backend.app.utils.db import get_db_cursor

class SystemDAO:
    """Data access for global store settings used by the backend to control the frontend."""

    DEFAULT_SETTINGS = {
        "setting_id": 1,
        "store_status": "OPEN",
        "reservations_enabled": 1,
        "ordering_enabled": 1,
        "pre_order_enabled": 1,
        "announcement_text": "",
        "announcement_type": "info",
        "opening_time": "11:00",
        "closing_time": "21:30",
    }

    def __init__(self, conn):
        self.conn = conn

    def _ensure_row(self):
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("SELECT * FROM store_settings WHERE setting_id = 1")
            row = cursor.fetchone()
            if row:
                return dict(row)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                INSERT INTO store_settings (
                    setting_id, store_status, reservations_enabled, ordering_enabled,
                    pre_order_enabled, announcement_text, announcement_type,
                    opening_time, closing_time, updated_at
                ) VALUES (1, 'OPEN', 1, 1, 1, '', 'info', '11:00', '21:30', ?)
            """, (now_str,))
            cursor.execute("SELECT * FROM store_settings WHERE setting_id = 1")
            row = cursor.fetchone()
            return dict(row) if row else dict(self.DEFAULT_SETTINGS, updated_at=now_str)

    def get_settings(self):
        """Returns the single store settings row, creating defaults if missing."""
        return self._ensure_row()

    def update_settings(self, fields: dict):
        """Updates allowed store setting fields and bumps updated_at."""
        self._ensure_row()
        allowed = {
            "store_status",
            "reservations_enabled",
            "ordering_enabled",
            "pre_order_enabled",
            "announcement_text",
            "announcement_type",
            "opening_time",
            "closing_time",
        }
        update_cols = []
        params = []
        for k, v in fields.items():
            if k in allowed:
                update_cols.append(f"{k} = ?")
                params.append(v)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
        update_cols.append("updated_at = ?")
        params.append(now_str)
        params.append(1)

        sql = f"UPDATE store_settings SET {', '.join(update_cols)} WHERE setting_id = ?"
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute(sql, tuple(params))
        return self.get_settings()

    def touch_updated_at(self):
        """Bumps updated_at so frontends know menu/table/config state changed."""
        self._ensure_row()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute(
                "UPDATE store_settings SET updated_at = ? WHERE setting_id = ?",
                (now_str, 1),
            )
