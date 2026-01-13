import random
import string
import secrets
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from backend.app.core.config import settings
from fastapi import Response
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()

def generate_otp(length: int = 6) -> str:
    otp = "".join(secrets.choice(string.digits) for _ in range(length))
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



def create_jwt_token(id: uuid.UUID, type: str = settings.COOKIE_ACCESS_NAME) -> str:
    if type == settings.COOKIE_ACCESS_NAME:
        expire_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    elif type == settings.COOKIE_REFRESH_NAME:
        expire_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        raise ValueError(f"Invalid token type: {type}")
    
    payload = {
        "id": str(id),
        "type": type,
        "exp": datetime.now(timezone.utc) + expire_delta,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str | None = None)-> None:
    cookie_settings = {
        "path": settings.COOKIE_PATH,
        "httponly": settings.COOKIE_HTTPONLY,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
    }

    access_cookie_settings = cookie_settings.copy()
    access_cookie_settings["max_age"] = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    response.set_cookie(
        settings.COOKIE_ACCESS_NAME,
        access_token,
        **access_cookie_settings
    )

    if refresh_token:
        refresh_cookie_settings = cookie_settings.copy()
        refresh_cookie_settings["max_age"] = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        response.set_cookie(
            settings.COOKIE_REFRESH_NAME,
            refresh_token,
            **refresh_cookie_settings
        )

    logged_in_cookie_settings = cookie_settings.copy()
    logged_in_cookie_settings["httponly"] = False
    logged_in_cookie_settings["max_age"] = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    response.set_cookie(
        settings.COOKIE_LOGGED_IN_NAME,
        "true",
        **logged_in_cookie_settings
    )


def delete_auth_cookies(response: Response) -> None:
    """Delete authentication cookies directly"""
    response.delete_cookie(settings.COOKIE_ACCESS_NAME)
    response.delete_cookie(settings.COOKIE_REFRESH_NAME)
    response.delete_cookie(settings.COOKIE_LOGGED_IN_NAME)


def create_password_reset_token(id: uuid.UUID) -> str:
    payload = {
        "id": str(id),
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)