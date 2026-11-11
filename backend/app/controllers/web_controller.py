import os
from flask import Blueprint, jsonify, send_from_directory, Response

web_bp = Blueprint("web", __name__)

DIST_WEB_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "dist_web")
)

@web_bp.route("/", methods=["GET"])
def serve_customer_index():
    """Serves the customer web frontend directly from the unified backend server."""
    index_path = os.path.join(DIST_WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(DIST_WEB_DIR, "index.html")
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "system": "Restaurant Reservation & Ordering System",
        "admin_console": "/admin",
        "api_docs": "/api/v1"
    }), 200

@web_bp.route("/_expo/<path:filename>", methods=["GET"])
def serve_expo_static(filename):
    return send_from_directory(os.path.join(DIST_WEB_DIR, "_expo"), filename)

@web_bp.route("/assets/<path:filename>", methods=["GET"])
def serve_expo_assets(filename):
    return send_from_directory(os.path.join(DIST_WEB_DIR, "assets"), filename)

@web_bp.route("/metadata.json", methods=["GET"])
def serve_metadata():
    return send_from_directory(DIST_WEB_DIR, "metadata.json")

@web_bp.route("/favicon.ico", methods=["GET"])
def serve_favicon():
    fav_path = os.path.join(DIST_WEB_DIR, "favicon.ico")
    if os.path.exists(fav_path):
        return send_from_directory(DIST_WEB_DIR, "favicon.ico")
    return Response(status=204)
