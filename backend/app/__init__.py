import os
from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.app.utils.db import get_connection, init_sqlite_db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)

    # Initialize SQLite database if needed
    if app.config.get("DB_TYPE") == "sqlite":
        conn = get_connection(config_class)
        init_sqlite_db(conn)
        conn.close()

    # Health check route
    @app.route("/api/v1/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "version": "1.0.0",
            "system": "Restaurant Reservation & Ordering System"
        }), 200

    # Register Blueprints
    from backend.app.controllers.menu_controller import menu_bp
    from backend.app.controllers.admin_menu_controller import admin_menu_bp
    from backend.app.controllers.auth_controller import auth_bp
    from backend.app.controllers.reservation_controller import reservation_bp
    from backend.app.controllers.admin_reservation_controller import admin_reservation_bp
    from backend.app.controllers.order_controller import order_bp
    from backend.app.controllers.admin_order_controller import admin_order_bp
    from backend.app.controllers.system_controller import system_bp
    from backend.app.controllers.admin_system_controller import admin_system_bp
    from backend.app.controllers.admin_table_controller import admin_table_bp
    from backend.app.controllers.admin_web_controller import admin_web_bp
    from backend.app.controllers.web_controller import web_bp
    app.register_blueprint(menu_bp)
    app.register_blueprint(admin_menu_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(admin_reservation_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_order_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(admin_system_bp)
    app.register_blueprint(admin_table_bp)
    app.register_blueprint(admin_web_bp)
    app.register_blueprint(web_bp)

    # Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"code": "NOT_FOUND", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_server_error(e):
        return jsonify({"code": "SERVER_ERROR", "message": "An internal error occurred"}), 500

    return app
