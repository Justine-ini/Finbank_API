from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from backend.app.api.main import api_router
from backend.app.core.config import settings
from contextlib import asynccontextmanager
from backend.app.core.db import init_db, engine
from backend.app.core.logging import get_logger
from backend.app.core.health import health_checker, ServiceStatus
import asyncio
import time


logger = get_logger()

async def startup_health_check(timeout: float=90.0) -> bool:
    try:
        async with asyncio.timeout(timeout):
            retry_intervals = [1,2,5,10,15]
            start_time = time.time()

            while True:
                is_healthy = await health_checker.wait_for_services()

                if is_healthy:
                    return True
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.error("Services failed health check during startup")

                wait_time = retry_intervals[min(len(retry_intervals) - 1, int(elapsed/10))]
                logger.warning(f"Services not healthy, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)

    except asyncio.TimeoutError:
        logger.error(f"Health check timed out after {timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"Error during startup health check: {e} seconds")
        return False
        



@asynccontextmanager 
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("Database initialized successfully!")

        await health_checker.add_service("database", health_checker.check_database)

        await health_checker.add_service("celery", health_checker.check_celery)

        await health_checker.add_service("redis", health_checker.check_redis)

        if not await startup_health_check():
            raise RuntimeError("Critical services failed to start")
        logger.info("All services initialized and healthy")
        yield
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        await engine.dispose()
        await health_checker.cleanup()
        raise 
    finally:
        logger.info("Shuting down application...")
        await engine.dispose()
        await health_checker.cleanup()



app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

@app.get("/health", response_model=dict)
async def health_check():
    try:
        health_status = await health_checker.check_all_services()

        if health_status["status"] == ServiceStatus.HEALTHY:
            status_code = status.HTTP_200_OK
        elif health_status["status"] == ServiceStatus.DEGRADED:
            status_code = status.HTTP_206_PARTIAL_CONTENT
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(status_code=status_code, content=health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_INTERNAL_SERVER_ERROR, 
            content={"status": ServiceStatus.UNHEALTHY, "error": str(e)},
        )


app.include_router(api_router,prefix=settings.API_V1_STR)


