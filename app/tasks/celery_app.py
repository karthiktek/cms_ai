from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "cms_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_track_started=True,
    task_time_limit=600,
)
celery_app.autodiscover_tasks(["app.tasks"], related_name="system")
