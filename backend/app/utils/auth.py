import time
import hmac
import hashlib
import json
import base64
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """Securely hash password using werkzeug default pbkdf2/scrypt."""
    return generate_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hash."""
    return check_password_hash(hashed_password, plain_password)

def generate_token(user_id: int, role: str, email: str, expires_in: int = 86400) -> str:
    """
    Generates a secure HMAC-SHA256 signed Token.
    Payload: user_id, role, email, exp
    """
    secret = current_app.config.get("SECRET_KEY", "dev-secret")
    payload = {
        "user_id": user_id,
        "role": role,
        "email": email,
        "exp": int(time.time()) + expires_in
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')
    
    signature = hmac.new(secret.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{payload_b64}.{sig_b64}"

def decode_token(token: str):
    """
    Decodes and verifies an HMAC token.
    Returns payload dict if valid, or None if expired/tampered.
    """
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        secret = current_app.config.get("SECRET_KEY", "dev-secret")

        # Verify signature
        expected_sig = hmac.new(secret.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + '=' * (-len(sig_b64) % 4))
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + '=' * (-len(payload_b64) % 4))
        payload = json.loads(payload_bytes.decode('utf-8'))

        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "error": "UNAUTHORIZED",
                "message": "Missing or invalid Authorization header"
            }), 401

        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_token(token)
        if not payload:
            return jsonify({
                "success": False,
                "error": "UNAUTHORIZED",
                "message": "Token is invalid or expired"
            }), 401

        request.current_user = payload
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "error": "UNAUTHORIZED",
                "message": "Missing or invalid Authorization header"
            }), 401

        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_token(token)
        if not payload:
            return jsonify({
                "success": False,
                "error": "UNAUTHORIZED",
                "message": "Token is invalid or expired"
            }), 401

        if payload.get("role") not in ("ADMIN", "STAFF"):
            return jsonify({
                "success": False,
                "error": "FORBIDDEN",
                "message": "Admin privileges required"
            }), 403

        request.current_user = payload
        return f(*args, **kwargs)
    return decorated_function
