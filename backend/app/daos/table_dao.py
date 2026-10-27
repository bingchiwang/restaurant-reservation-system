from backend.app.utils.db import get_db_cursor

class TableDAO:
    def __init__(self, conn):
        self.conn = conn

    def get_all_tables(self, status="ACTIVE"):
        """
        Retrieves dining tables with given status, ordered by capacity ASC, table_id ASC.
        """
        with get_db_cursor(self.conn) as cursor:
            if status:
                cursor.execute("""
                    SELECT table_id, table_name, capacity, status, created_at, updated_at
                    FROM dining_tables
                    WHERE status = ?
                    ORDER BY capacity ASC, table_id ASC
                """, (status,))
            else:
                cursor.execute("""
                    SELECT table_id, table_name, capacity, status, created_at, updated_at
                    FROM dining_tables
                    ORDER BY capacity ASC, table_id ASC
                """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_conflicting_table_ids(self, start_at: str, end_at: str):
        """
        Retrieves table IDs that have active (non-cancelled) reservations
        overlapping with [start_at, end_at).
        Overlap condition: r.start_at < end_at AND r.end_at > start_at
        """
        with get_db_cursor(self.conn) as cursor:
            cursor.execute("""
                SELECT DISTINCT rt.table_id
                FROM reservation_tables rt
                JOIN reservations r ON rt.reservation_id = r.reservation_id
                WHERE r.status != 'CANCELLED'
                  AND r.start_at < ?
                  AND r.end_at > ?
            """, (end_at, start_at))
            rows = cursor.fetchall()
            return set(row["table_id"] if isinstance(row, dict) else row[0] for row in rows)

    def create_table(self, table_name: str, capacity: int, status: str = "ACTIVE"):
        """
        Creates a new dining table.
        """
        with get_db_cursor(self.conn, commit=True) as cursor:
            cursor.execute("""
                INSERT INTO dining_tables (table_name, capacity, status)
                VALUES (?, ?, ?)
            """, (table_name.strip(), capacity, status))
            return cursor.lastrowid
