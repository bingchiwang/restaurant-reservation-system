from backend.app.daos.table_dao import TableDAO
from backend.app.daos.system_dao import SystemDAO

class TableService:
    """Business logic for REQ-013 dining table management."""

    VALID_STATUSES = {"ACTIVE", "MAINTENANCE", "DISABLED"}

    def __init__(self, conn):
        self.conn = conn
        self.table_dao = TableDAO(conn)
        self.system_dao = SystemDAO(conn)

    def list_tables(self, status=None):
        return self.table_dao.get_all_tables(status=status)

    def create_table(self, table_name: str, capacity, status: str = "ACTIVE"):
        if not table_name or not str(table_name).strip():
            raise ValueError("Table name cannot be empty")

        try:
            cap_int = int(capacity)
        except (ValueError, TypeError):
            raise ValueError("Capacity must be a valid integer")
        if cap_int <= 0:
            raise ValueError("Capacity must be greater than 0")

        norm_status = str(status or "ACTIVE").strip().upper()
        if norm_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid table status: {norm_status}")

        table_id = self.table_dao.create_table(str(table_name).strip(), cap_int, norm_status)
        self.system_dao.touch_updated_at()
        return self.table_dao.get_table_by_id(table_id)

    def update_table(self, table_id: int, fields: dict):
        existing = self.table_dao.get_table_by_id(table_id)
        if not existing:
            raise LookupError(f"Table {table_id} not found")

        cleaned = {}
        if "table_name" in fields:
            name = str(fields["table_name"] or "").strip()
            if not name:
                raise ValueError("Table name cannot be empty")
            cleaned["table_name"] = name

        if "capacity" in fields:
            try:
                cap_int = int(fields["capacity"])
            except (ValueError, TypeError):
                raise ValueError("Capacity must be a valid integer")
            if cap_int <= 0:
                raise ValueError("Capacity must be greater than 0")
            cleaned["capacity"] = cap_int

        if "status" in fields:
            norm_status = str(fields["status"] or "").strip().upper()
            if norm_status not in self.VALID_STATUSES:
                raise ValueError(f"Invalid table status: {norm_status}")
            cleaned["status"] = norm_status

        if cleaned:
            self.table_dao.update_table(table_id, cleaned)
            self.system_dao.touch_updated_at()

        return self.table_dao.get_table_by_id(table_id)
