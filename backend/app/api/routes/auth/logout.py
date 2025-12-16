from fastapi import APIRouter, Response, status, HTTPException
from backend.app.auth.utils import delete_auth_cookies
from backend.app.core.logging import get_logger

logger = get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> dict:
    try:
        delete_auth_cookies(response)
        logger.info("User logged out successfully.")
        return {"message": "Successfully logged out."}
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to log out user.",
                "action": "Please try again later."
            }
        )