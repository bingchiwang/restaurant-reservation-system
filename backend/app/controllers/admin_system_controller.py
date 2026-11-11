from flask import Blueprint, request, jsonify
from backend.app.utils.auth import admin_required
from backend.app.facades.system_facade import SystemFacade

admin_system_bp = Blueprint("admin_system", __name__, url_prefix="/api/v1/admin/system")

@admin_system_bp.route("/config", methods=["GET"])
@admin_required
def admin_get_config():
    """Admin endpoint to inspect current frontend control settings."""
    facade = SystemFacade()
    data = facade.admin_get_config()
    return jsonify({
        "success": True,
        "data": data
    }), 200

@admin_system_bp.route("/config", methods=["PATCH"])
@admin_required
def admin_update_config():
    """Admin endpoint to update frontend control settings (open/closed, toggles, banner, hours)."""
    data = request.get_json() or {}
    facade = SystemFacade()
    try:
        updated = facade.admin_update_config(data)
        return jsonify({
            "success": True,
            "message": "System configuration updated",
            "data": updated
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400
