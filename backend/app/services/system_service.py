from datetime import datetime
from backend.app.daos.system_dao import SystemDAO
from backend.app.daos.table_dao import TableDAO

class SystemService:
    """Business logic for backend-to-frontend store controls and configuration."""

    VALID_STORE_STATUSES = {"OPEN", "CLOSED", "MAINTENANCE"}
    VALID_ANNOUNCEMENT_TYPES = {"info", "warning", "danger"}

    def __init__(self, conn):
        self.conn = conn
        self.system_dao = SystemDAO(conn)
        self.table_dao = TableDAO(conn)

    @staticmethod
    def _format_settings(row: dict) -> dict:
        return {
            "store_status": row.get("store_status", "OPEN"),
            "reservations_enabled": bool(row.get("reservations_enabled", 1)),
            "ordering_enabled": bool(row.get("ordering_enabled", 1)),
            "pre_order_enabled": bool(row.get("pre_order_enabled", 1)),
            "announcement_text": row.get("announcement_text") or "",
            "announcement_type": row.get("announcement_type") or "info",
            "opening_time": row.get("opening_time") or "11:00",
            "closing_time": row.get("closing_time") or "21:30",
            "updated_at": str(row.get("updated_at") or ""),
        }

    def get_settings(self) -> dict:
        row = self.system_dao.get_settings()
        return self._format_settings(row)

    def get_public_config(self) -> dict:
        """Returns public storefront controls and active dining tables."""
        config = self.get_settings()
        active_tables = self.table_dao.get_all_tables(status="ACTIVE")
        config["active_tables"] = [
            {
                "table_id": t["table_id"],
                "table_name": t["table_name"],
                "capacity": t["capacity"],
            }
            for t in active_tables
        ]
        return config

    def update_settings(self, fields: dict) -> dict:
        """Validates and updates backend storefront control settings."""
        if not isinstance(fields, dict):
            raise ValueError("Invalid settings payload")

        cleaned = {}

        if "store_status" in fields:
            status = str(fields["store_status"]).strip().upper()
            if status not in self.VALID_STORE_STATUSES:
                raise ValueError(f"Invalid store_status: must be one of {sorted(self.VALID_STORE_STATUSES)}")
            cleaned["store_status"] = status

        for bool_key in ("reservations_enabled", "ordering_enabled", "pre_order_enabled"):
            if bool_key in fields:
                cleaned[bool_key] = 1 if bool(fields[bool_key]) else 0

        if "announcement_text" in fields:
            text = "" if fields["announcement_text"] is None else str(fields["announcement_text"]).strip()
            if len(text) > 500:
                raise ValueError("Announcement text cannot exceed 500 characters")
            cleaned["announcement_text"] = text

        if "announcement_type" in fields:
            atype = str(fields["announcement_type"]).strip().lower()
            if atype not in self.VALID_ANNOUNCEMENT_TYPES:
                raise ValueError(f"Invalid announcement_type: must be one of {sorted(self.VALID_ANNOUNCEMENT_TYPES)}")
            cleaned["announcement_type"] = atype

        current = self.system_dao.get_settings()
        opening_str = str(fields.get("opening_time", current["opening_time"])).strip()
        closing_str = str(fields.get("closing_time", current["closing_time"])).strip()

        if "opening_time" in fields or "closing_time" in fields:
            try:
                open_t = datetime.strptime(opening_str, "%H:%M").time()
                close_t = datetime.strptime(closing_str, "%H:%M").time()
            except ValueError:
                raise ValueError("opening_time and closing_time must be in HH:MM format (e.g. 11:00)")
            if open_t >= close_t:
                raise ValueError("opening_time must be earlier than closing_time")
            if "opening_time" in fields:
                cleaned["opening_time"] = opening_str
            if "closing_time" in fields:
                cleaned["closing_time"] = closing_str

        if not cleaned:
            return self.get_public_config()

        self.system_dao.update_settings(cleaned)
        return self.get_public_config()
