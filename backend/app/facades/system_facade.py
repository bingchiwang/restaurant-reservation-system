from flask import has_app_context, current_app
from backend.app.utils.db import get_connection
from backend.app.services.system_service import SystemService

class SystemFacade:
    """Facade coordinating public and admin storefront configuration."""

    def __init__(self, conn=None):
        self._external_conn = conn

    def _get_service(self):
        if self._external_conn:
            conn = self._external_conn
        else:
            config = current_app.config if has_app_context() else None
            conn = get_connection(config) if config else get_connection()
        return conn, SystemService(conn)

    def get_public_config(self) -> dict:
        conn, service = self._get_service()
        try:
            return service.get_public_config()
        finally:
            if not self._external_conn:
                conn.close()

    def admin_get_config(self) -> dict:
        conn, service = self._get_service()
        try:
            return service.get_public_config()
        finally:
            if not self._external_conn:
                conn.close()

    def admin_update_config(self, fields: dict) -> dict:
        conn, service = self._get_service()
        try:
            return service.update_settings(fields)
        finally:
            if not self._external_conn:
                conn.close()
