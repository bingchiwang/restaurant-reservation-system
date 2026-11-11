from flask import Blueprint, render_template

admin_web_bp = Blueprint("admin_web", __name__)

@admin_web_bp.route("/admin", methods=["GET"])
def admin_dashboard():
    """Renders the backend-hosted Admin Control Center UI."""
    return render_template("admin.html")
