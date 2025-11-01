from typing import AsyncGenerator
from app.core.config import settings
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.logging import get_logger


logger = get_logger()

engine = create_async_engine(settings.DATABASE_URL)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_session() -> AsyncGenerator[AsyncSession,None]:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"An error occured while getting the database session:{e}")
            await session.rollback()
            raise 
        finally:
            await session.close()

async def init_db() -> None:
    pass