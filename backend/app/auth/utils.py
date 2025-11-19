import random
import string
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from backend.app.core.config import settings
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()

def generate_otp(length: int = 6)-> str:
    otp = "".join(random.choices(string.digits, k=length))
    return otp


def generate_password_hash(password: str)-> str:
    return _ph.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False
    
def generate_username()-> str:
    bank_name = settings.SITE_NAME
    words = bank_name.split()
    prefix = "".join([word[0] for word in words]).upper()
    remaining_length = 12 - len(prefix) - 1
    random_string = "".join(random.choices(string.ascii_uppercase + string.digits, k=remaining_length))
    username = f"{prefix}-{random_string}"
    return username

def create_activation_token(id: uuid.UUID)-> str:
    payload = {
        "id": str(id),
        "type": "activation",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACTIVATION_TOKEN_EXPIRATION_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)