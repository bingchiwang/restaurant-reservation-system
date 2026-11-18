from flask import Blueprint, request, jsonify
from backend.app.facades.auth_facade import AuthFacade
from backend.app.utils.auth import generate_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

def _handle_login(member_only: bool):
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
        result = facade.login(email, password, member_only=member_only)
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

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    REQ-011: 通用登入端點（管理員與會員登入）
    """
    return _handle_login(member_only=False)

@auth_bp.route("/member/login", methods=["POST"])
def member_login():
    """
    REQ-011: 顧客前端專用會員登入（嚴格限制僅允許 MEMBER 角色，阻擋管理員登入）
    """
    return _handle_login(member_only=True)

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
        token = generate_token(
            user_id=user["user_id"],
            role=user["role"],
            email=user["email"]
        )
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "data": {
                "user_id": user["user_id"],
                "email": user["email"],
                "display_name": user["display_name"],
                "role": user["role"],
                "token": token
            }
        }), 201
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": str(e)
        }), 400

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    REQ-011: 會員登出
    """
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200
