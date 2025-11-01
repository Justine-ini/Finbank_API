from fastapi import APIRouter
from app.core.logging import get_logger

logger=get_logger()

router = APIRouter(prefix="/home")
@router.get("/")
def home():
    return {"message": "Welcome to Finbank API"}

