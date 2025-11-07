import asyncio
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime, timedelta, timezone
from enum import Enum
from sqlalchemy import text
from backend.app.core.db import async_session
from backend.app.core.celery_app import celery_app
from backend.app.core.logging import get_logger


logger = get_logger()

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    STARTING = "starting"
    DOWN = "down"

class HealthCheck:
    def __init__(self):
        self._services: Dict[str, ServiceStatus] = {}
        self._check_functions: Dict[str, Callable[[], Awaitable[bool]]] = {}
        self._last_check: Dict[str, datetime] = {}
        self._timeouts: Dict[str, float] = {}
        self._retry_delays: Dict[str, float] = {}
        self._max_retries: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self. _dependencies: Dict[str, set[str]] = {}

        self._cache_duration: timedelta = timedelta(seconds=25)
        self._cache_status: Optional[Dict[str, Any]] = None
        self._last_check_time: Optional[datetime] = None

    async def validate_dependencies(self, service_name: str, depends_on: list[str])-> None:
        if not depends_on:
            return
        
        for dep in depends_on:
            if dep not in self._services:
                raise ValueError(
                    f"Dependency '{dep}' not registered for service '{service_name}'"
                )

    async def add_service(
            self, service_name: str, check_function: Callable[[], Awaitable[bool]], timeout: float=5.0, retry_delay: float = 1.0, max_retries: int = 3, depends_on: list[str] | None = None
    )-> None:
        self._services[service_name] = ServiceStatus.STARTING
        self._check_functions[service_name] = check_function
        self._timeouts[service_name] = timeout
        self._retry_delays[service_name] = retry_delay
        self._max_retries[service_name] = max_retries
        self._last_check[service_name] = datetime.now(timezone.utc)

        if depends_on:
            await self.validate_dependencies(service_name, depends_on)
            self._dependencies[service_name] = set(depends_on)
            logger.info(
                f"Service '{service_name}' registered with dependencies: {depends_on}"
            )

    async def check_database(self)-> bool:
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
                await session.commit()

                self._last_check["database"] = datetime.now(timezone.utc)
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        
    async def check_redis(self) -> bool:
        try:
            redis_client = celery_app.backend.client
            redis_client.ping()
            self._last_check["redis"] = datetime.now(timezone.utc)
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
        
    async def check_celery(self)-> bool:
        try:
            inspect = celery_app.control.inspect()
            workers = inspect.ping()

            if not workers:
                conn = celery_app.connection()
                try:
                    conn.ensure_connection(max_retries=3)
                    logger.warning("No celery workers found, but Rabbitmq is reacheable")
                    self._last_check["celery"] = datetime.now(timezone.utc)
                    return True
                finally:
                    conn.close()

            self._last_check["celery"] = datetime.now(timezone.utc)
            return True

        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return False

    async def check_service_health(self, service_name: str, max_retries: int=3) -> ServiceStatus:
        if service_name in self._dependencies:
            for dep in self._dependencies[service_name]:
                dep_status = await self.check_service_health(dep)
                if dep_status != ServiceStatus.HEALTHY:
                    logger.error(
                        f"Dependency {dep} not healthy for service {service_name}"
                    )
                    return ServiceStatus.DEGRADED
        
        if service_name not in self._check_functions:
            raise ValueError(f"Unknown service: {service_name}")
        check_func = self._check_functions[service_name]
        timeout = self._timeouts.get(service_name, 5.0)
        max_retries = self._max_retries[service_name]
        retry_delay = self._retry_delays[service_name]

        metrics = {"attempts": 0, "total_delay": 0.0, "last_error": None}

        for attempt in range(max_retries):
            metrics["attempts"] += 1
            try:
                async with asyncio.timeout(timeout):
                    is_healthy = await check_func()

                    if is_healthy:
                        async with self._lock:
                            self._services[service_name] = ServiceStatus.HEALTHY
                            self._last_check[service_name] = datetime.now()

                            if attempt > 0:
                                logger.info(f"Service {service_name} recovered after {metrics["attempts"]} attempts")

                        return ServiceStatus.HEALTHY
                    
                    async with self._lock:
                        self._services[service_name] = ServiceStatus.DEGRADED
            except asyncio.TimeoutError:
                metrics["last_error"] = f"Timeout after {timeout}"
                if attempt == max_retries - 1:
                    logger.warning(f"Health check timeout for {service_name} after all retries")
            
            except Exception as e:
                metrics["last_error"] = str(e)
                if attempt == max_retries - 1:
                    logger.error(f"Health check failed for {service_name}: {e}")

            metrics["total_delay"] += retry_delay
            await asyncio.sleep(retry_delay)

        async with self._lock:
            self._services[service_name] = ServiceStatus.UNHEALTHY
            logger.error(f"Service {service_name} unhealthy after {max_retries} attempts: {metrics['last_error']}")
        
        return ServiceStatus.UNHEALTHY
    
    async def check_all_services(self) -> Dict[str, Any]:
        current_time =  datetime.now(timezone.utc)

        if (
            self._cache_status is not None 
            and self._last_check_time is not None
            and (current_time - self._last_check_time) < self._cache_duration
        ):
            return self._cache_status
        
        async with self._lock:
            services = list(self._services.keys())
        tasks = [self.check_service_health(service) for service in services]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_status = {
            "status": ServiceStatus.HEALTHY,
            "timestamp": current_time.isoformat(),
            "services" : {}
        }

        for service, result in zip(services, results):
            if isinstance(result, Exception):
                health_status["services"][service] = {
                    "status": ServiceStatus.UNHEALTHY,
                    "error": str(result),
                    "last_check": self._last_check[service].isoformat()
                }
                health_status["status"] = ServiceStatus.DEGRADED
            else:
                health_status["services"][service] = {
                    "status": result,
                    "last_check": self._last_check[service].isoformat()
                }
                if result != ServiceStatus.HEALTHY:
                   health_status["status"] = ServiceStatus.DEGRADED
        self._cache_status = health_status
        self._last_check_time = current_time  

        return health_status
    
    async def wait_for_services(self, timeout: float=30.0) -> bool:
        try:
            start_time = datetime.now()
            while(datetime.now() - start_time) < timedelta(seconds=timeout):
                status = await self.check_all_services()
                if status["status"] == ServiceStatus.HEALTHY:
                    return True
                await asyncio.sleep(1)
            return False
        except Exception as e:
            logger.error(f"Error waiting for services: {e}")
            return False
                
    async def cleanup(self) -> None:
        async with self._lock:
            self._services.clear()
            self._check_functions.clear()
            self._last_check.clear()
            self._timeouts.clear()
            self._retry_delays.clear()
            self._max_retries.clear()


health_checker = HealthCheck()




