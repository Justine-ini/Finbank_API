from fastapi import FastAPI
from backend.app.api.main import api_router
from backend.app.core.config import settings
from contextlib import asynccontextmanager
from backend.app.core.db import init_db

@asynccontextmanager 
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.include_router(api_router,prefix=settings.API_V1_STR)


