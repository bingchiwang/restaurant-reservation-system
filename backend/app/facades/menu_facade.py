from flask import has_app_context, current_app
from backend.app.utils.db import get_connection
from backend.app.daos.menu_dao import MenuDAO
from backend.app.services.menu_service import MenuService

class MenuFacade:
    def __init__(self, conn=None):
        self._external_conn = conn

    def _get_service(self):
        if self._external_conn:
            conn = self._external_conn
        else:
            config = current_app.config if has_app_context() else None
            conn = get_connection(config) if config else get_connection()
        dao = MenuDAO(conn)
        service = MenuService(dao)
        return conn, service

    def list_categories(self, status="ACTIVE"):
        """
        Retrieves all menu categories for customer browsing.
        """
        conn, service = self._get_service()
        try:
            return service.get_categories(status=status)
        finally:
            if not self._external_conn:
                conn.close()

    def list_menu_items(self, category_id=None, only_available=True):
        """
        Retrieves available menu items for customer browsing.
        """
        conn, service = self._get_service()
        try:
            return service.get_menu_items(category_id=category_id, only_available=only_available)
        finally:
            if not self._external_conn:
                conn.close()

    def get_menu_item_detail(self, item_id):
        """
        Retrieves details for a specific item.
        """
        conn, service = self._get_service()
        try:
            return service.get_item_by_id(item_id)
        finally:
            if not self._external_conn:
                conn.close()
