from pydantic import BaseModel


class RateLimitConfig(BaseModel):
    """
    Configuration for rate limiting.

    Attributes:
        max_requests (int): Maximum number of requests allowed within the specified time window.
        window_seconds (int): Time window in seconds during which the requests are counted.
        block_on_exceed (bool): Whether to block requests that exceed the limit. Defaults to True.
    """

    max_requests: int
    window_seconds: int
    block_on_exceed: bool = True

DEFAULT_RATE_LIMIT_CONFIG: dict[str, RateLimitConfig] = {
    "/api/v1/auth/login/request-otp": RateLimitConfig(
        max_requests=2, 
        window_seconds=300
    ),
    "/api/v1/auth/register": RateLimitConfig(
        max_requests=3, 
        window_seconds=3600
    ),
    "/api/v1/auth/request-password-reset": RateLimitConfig(
        max_requests=3, 
        window_seconds=3600
    ),
    "/api/v1/auth/reset-password/{token}": RateLimitConfig(
        max_requests=3, 
        window_seconds=3600
    ),
    "/api/v1/bank-account/transfer/initiate": RateLimitConfig(
        max_requests=10, 
        window_seconds=3600
    ),
    "/api/v1/bank-account/withdraw": RateLimitConfig(
        max_requests=10, 
        window_seconds=3600
    ),
    "/api/v1/bank-account/deposit": RateLimitConfig(
        max_requests=20, 
        window_seconds=3600
    ),
    "/api/v1/virtual-card/create": RateLimitConfig(
        max_requests=5, 
        window_seconds=86400
    ),
    "/api/v1/virtual-card/{card_id}/top-up": RateLimitConfig(
        max_requests=20, 
        window_seconds=3600
    ),
    "/api/v1/profile/upload/{image_type}": RateLimitConfig(
        max_requests=10, 
        window_seconds=3600
    ),
    "/api/v1/bank-account/statement/generate": RateLimitConfig(
        max_requests=5, 
        window_seconds=3600
    ),
    "/health": RateLimitConfig(
        max_requests=500, 
        window_seconds=60,
        block_on_exceed=False
    ),
    "default": RateLimitConfig(
        max_requests=100, 
        window_seconds=60,
        block_on_exceed=False
    )
    
}

RATE_LIMIT_WHITELIST = {"/health"}
    
