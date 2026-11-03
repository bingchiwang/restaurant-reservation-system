from flask import has_app_context, current_app
from backend.app.utils.db import get_connection
from backend.app.services.order_service import OrderService

class OrderFacade:
    def __init__(self, conn=None):
        self._external_conn = conn

    def _get_service(self):
        if self._external_conn:
            conn = self._external_conn
        else:
            config = current_app.config if has_app_context() else None
            conn = get_connection(config) if config else get_connection()
        service = OrderService(conn)
        return conn, service

    def create_dine_in_order(self, table_id: int, items: list, user_id=None):
        """
        REQ-007: 建立現場點餐訂單
        """
        conn, service = self._get_service()
        try:
            return service.create_order(
                order_type="DINE_IN",
                items_input=items,
                user_id=user_id,
                table_id=table_id,
                status="PENDING"
            )
        finally:
            if not self._external_conn:
                conn.close()

    def get_order(self, order_id: int):
        conn, service = self._get_service()
        try:
            return service.get_order_details(order_id)
        finally:
            if not self._external_conn:
                conn.close()

    def admin_list_orders(self, status=None, reservation_id=None, table_id=None, date_str=None, limit=50, offset=0):
        conn, service = self._get_service()
        try:
            return service.list_orders(status=status, reservation_id=reservation_id, table_id=table_id, date_str=date_str, limit=limit, offset=offset)
        finally:
            if not self._external_conn:
                conn.close()

    def admin_update_order_status(self, order_id: int, new_status: str):
        conn, service = self._get_service()
        try:
            return service.update_order_status(order_id, new_status)
        finally:
            if not self._external_conn:
                conn.close()
