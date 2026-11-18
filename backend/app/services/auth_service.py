import re
from datetime import datetime, date
from backend.app.utils.auth import verify_password, hash_password, generate_token

class AuthService:
    VALID_GENDERS = {"MALE", "FEMALE", "OTHER", "PREFER_NOT_TO_SAY"}

    def __init__(self, user_dao):
        self.user_dao = user_dao

    @staticmethod
    def _public_user(user: dict) -> dict:
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "phone": user.get("phone") or "",
            "gender": user.get("gender") or "",
            "birthday": str(user.get("birthday") or ""),
            "role": user["role"],
            "status": user.get("status", "ACTIVE"),
            "created_at": str(user.get("created_at") or ""),
        }

    @staticmethod
    def _validate_phone(phone) -> str:
        raw = str(phone or "").strip()
        if not raw:
            raise ValueError("Phone number is required")
        if not re.match(r"^[0-9+\-\s()]{8,20}$", raw):
            raise ValueError("Invalid phone number format")
        digits = re.sub(r"\D", "", raw)
        if len(digits) < 8 or len(digits) > 15:
            raise ValueError("Phone number must contain between 8 and 15 digits")
        return raw

    @classmethod
    def _validate_gender(cls, gender) -> str:
        norm = str(gender or "").strip().upper()
        if not norm:
            raise ValueError("Gender is required")
        if norm not in cls.VALID_GENDERS:
            raise ValueError(f"Invalid gender: must be one of {sorted(cls.VALID_GENDERS)}")
        return norm

    @staticmethod
    def _validate_birthday(birthday) -> str:
        bday_str = str(birthday or "").strip()
        if not bday_str:
            raise ValueError("Birthday is required")
        try:
            parsed = datetime.strptime(bday_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid birthday format: expected YYYY-MM-DD")
        if parsed > date.today():
            raise ValueError("Birthday cannot be in the future")
        if parsed < date(1900, 1, 1):
            raise ValueError("Invalid birthday year")
        return parsed.strftime("%Y-%m-%d")

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

    def register_user(
        self,
        email: str,
        password: str,
        display_name: str,
        phone: str = None,
        gender: str = None,
        birthday: str = None,
        role: str = "MEMBER",
    ):
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

        clean_phone = self._validate_phone(phone)
        clean_gender = self._validate_gender(gender)
        clean_birthday = self._validate_birthday(birthday)

        existing = self.user_dao.get_by_email(clean_email)
        if existing:
            raise ValueError("Email is already registered")

        pwd_hash = hash_password(password)
        user_id = self.user_dao.create_user(
            email=clean_email,
            password_hash=pwd_hash,
            display_name=clean_name,
            phone=clean_phone,
            gender=clean_gender,
            birthday=clean_birthday,
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

        if "phone" in fields:
            cleaned["phone"] = self._validate_phone(fields["phone"])

        if "gender" in fields:
            cleaned["gender"] = self._validate_gender(fields["gender"])

        if "birthday" in fields:
            cleaned["birthday"] = self._validate_birthday(fields["birthday"])

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
