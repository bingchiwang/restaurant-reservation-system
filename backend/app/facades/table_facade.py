from flask import has_app_context, current_app
from backend.app.utils.db import get_connection
from backend.app.services.table_service import TableService

class TableFacade:
    """Facade for dining table management."""

    def __init__(self, conn=None):
        self._external_conn = conn

    def _get_service(self):
        if self._external_conn:
            conn = self._external_conn
        else:
            config = current_app.config if has_app_context() else None
            conn = get_connection(config) if config else get_connection()
        return conn, TableService(conn)

    def list_tables(self, status=None):
        conn, service = self._get_service()
        try:
            return service.list_tables(status=status)
        finally:
            if not self._external_conn:
                conn.close()

    def create_table(self, table_name: str, capacity, status: str = "ACTIVE"):
        conn, service = self._get_service()
        try:
            return service.create_table(table_name=table_name, capacity=capacity, status=status)
        finally:
            if not self._external_conn:
                conn.close()

    def update_table(self, table_id: int, fields: dict):
        conn, service = self._get_service()
        try:
            return service.update_table(table_id=table_id, fields=fields)
        finally:
            if not self._external_conn:
                conn.close()
