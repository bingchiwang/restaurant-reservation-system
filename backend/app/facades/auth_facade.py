from flask import has_app_context, current_app
from backend.app.utils.db import get_connection
from backend.app.daos.user_dao import UserDAO
from backend.app.services.auth_service import AuthService

class AuthFacade:
    def __init__(self, conn=None):
        self._external_conn = conn

    def _get_service(self):
        if self._external_conn:
            conn = self._external_conn
        else:
            config = current_app.config if has_app_context() else None
            conn = get_connection(config) if config else get_connection()
        dao = UserDAO(conn)
        service = AuthService(dao)
        return conn, service

    def login(self, email: str, password: str):
        conn, service = self._get_service()
        try:
            return service.authenticate(email, password)
        finally:
            if not self._external_conn:
                conn.close()

    def register(self, email: str, password: str, display_name: str, role: str = "MEMBER"):
        conn, service = self._get_service()
        try:
            return service.register_user(email, password, display_name, role)
        finally:
            if not self._external_conn:
                conn.close()
