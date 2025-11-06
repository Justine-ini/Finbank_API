from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "worker",
    broker=f"ampq://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_POST}//",

    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
)

celery_app.conf.update(
    task_serializer="json",   
    task_track_started=True,
    result_serializer="json", 
    accept_content=["application/json"],
    result_backend_max_retries=10,
    result_extended=True,
    result_backend_always_retry=True,
    result_expires=3600,
    task_send_sent_event=True,
    task_time_limit=5 * 60,
    task_soft_time_limit=5 * 60,
    worker_send_task_events=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=300,
    task_max_retries=3,
    task_default_queue="Finbank_task",
    task_create_missing_queues=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=50000,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s]%(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)

celery_app.autodiscover_tasks(
    packages=["backend.app.core.emails"],
    related_name="tasks",
    force=True,
)