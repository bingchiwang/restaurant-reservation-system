from flask import Blueprint, request, jsonify
from backend.app.facades.auth_facade import AuthFacade

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    REQ-011: 會員與管理員登入
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "Email and password are required"
        }), 400

    facade = AuthFacade()
    try:
        result = facade.login(email, password)
        return jsonify({
            "success": True,
            "data": result
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "UNAUTHORIZED",
            "message": str(e)
        }), 401
    except PermissionError as e:
        return jsonify({
            "success": False,
            "error": "FORBIDDEN",
            "message": str(e)
        }), 403

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    REQ-011: 會員註冊
    """
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    display_name = data.get("display_name")

    facade = AuthFacade()
    try:
        user = facade.register(email, password, display_name, role="MEMBER")
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "data": {
                "user_id": user["user_id"],
                "email": user["email"],
                "display_name": user["display_name"],
                "role": user["role"]
            }
        }), 201
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400
