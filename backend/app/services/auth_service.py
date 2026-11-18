from backend.app.utils.auth import verify_password, hash_password, generate_token

class AuthService:
    def __init__(self, user_dao):
        self.user_dao = user_dao

    @staticmethod
    def _public_user(user: dict) -> dict:
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "role": user["role"],
            "status": user.get("status", "ACTIVE"),
            "created_at": str(user.get("created_at") or ""),
        }

    def authenticate(self, email: str, password: str, member_only: bool = False):
        if not email or not password:
            raise ValueError("Email and password are required")

        user = self.user_dao.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        if user.get("status") != "ACTIVE":
            raise PermissionError("Account is not active")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password")

        if member_only and user.get("role") != "MEMBER":
            raise PermissionError("Customer portal only allows MEMBER accounts; administrators must sign in via /admin")

        token = generate_token(
            user_id=user["user_id"],
            role=user["role"],
            email=user["email"]
        )

        return {
            "token": token,
            "user": self._public_user(user)
        }

    def register_user(self, email: str, password: str, display_name: str, role: str = "MEMBER"):
        if not email or not password or not display_name:
            raise ValueError("Email, password, and display_name are required")

        clean_email = str(email).strip().lower()
        if "@" not in clean_email or "." not in clean_email.split("@")[-1]:
            raise ValueError("Invalid email format")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")

        clean_name = str(display_name).strip()
        if not clean_name:
            raise ValueError("Display name cannot be empty")

        existing = self.user_dao.get_by_email(clean_email)
        if existing:
            raise ValueError("Email is already registered")

        pwd_hash = hash_password(password)
        user_id = self.user_dao.create_user(
            email=clean_email,
            password_hash=pwd_hash,
            display_name=clean_name,
            role=role,
            status="ACTIVE"
        )
        return self.user_dao.get_by_id(user_id)

    def get_profile(self, user_id: int) -> dict:
        user = self.user_dao.get_by_id(user_id)
        if not user:
            raise LookupError("User not found")
        return self._public_user(user)

    def update_profile(self, user_id: int, fields: dict) -> dict:
        user = self.user_dao.get_by_id(user_id)
        if not user:
            raise LookupError("User not found")

        cleaned = {}
        if "display_name" in fields:
            name = str(fields["display_name"] or "").strip()
            if not name:
                raise ValueError("Display name cannot be empty")
            cleaned["display_name"] = name

        if "new_password" in fields and fields["new_password"]:
            current_pwd = fields.get("current_password", "")
            if not current_pwd or not verify_password(current_pwd, user["password_hash"]):
                raise ValueError("Current password is incorrect")
            if len(str(fields["new_password"])) < 6:
                raise ValueError("New password must be at least 6 characters")
            cleaned["password_hash"] = hash_password(str(fields["new_password"]))

        if cleaned:
            self.user_dao.update_user(user_id, cleaned)

        return self.get_profile(user_id)
