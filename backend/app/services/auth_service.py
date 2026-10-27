from backend.app.utils.auth import verify_password, hash_password, generate_token

class AuthService:
    def __init__(self, user_dao):
        self.user_dao = user_dao

    def authenticate(self, email: str, password: str):
        if not email or not password:
            raise ValueError("Email and password are required")

        user = self.user_dao.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        if user.get("status") != "ACTIVE":
            raise PermissionError("Account is not active")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password")

        token = generate_token(
            user_id=user["user_id"],
            role=user["role"],
            email=user["email"]
        )

        return {
            "token": token,
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "display_name": user["display_name"],
                "role": user["role"]
            }
        }

    def register_user(self, email: str, password: str, display_name: str, role: str = "MEMBER"):
        if not email or not password or not display_name:
            raise ValueError("Email, password, and display_name are required")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")

        existing = self.user_dao.get_by_email(email)
        if existing:
            raise ValueError("Email is already registered")

        pwd_hash = hash_password(password)
        user_id = self.user_dao.create_user(
            email=email,
            password_hash=pwd_hash,
            display_name=display_name.strip(),
            role=role,
            status="ACTIVE"
        )
        return self.user_dao.get_by_id(user_id)
