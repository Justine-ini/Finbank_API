from fastapi import APIRouter
from backend.app.core.logging import get_logger

logger=get_logger()

router = APIRouter(prefix="/home")
@router.get("/")
def home():
    return {"message": "Welcome to Finbank API"}

