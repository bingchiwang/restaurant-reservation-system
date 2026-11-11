from flask import Blueprint, jsonify
from backend.app.facades.system_facade import SystemFacade

system_bp = Blueprint("system", __name__, url_prefix="/api/v1/system")

@system_bp.route("/config", methods=["GET"])
def get_public_system_config():
    """Returns storefront operating controls, announcements, hours, and active tables."""
    facade = SystemFacade()
    data = facade.get_public_config()
    return jsonify({
        "success": True,
        "data": data
    }), 200
