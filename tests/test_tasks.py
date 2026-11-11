from app.tasks.celery_app import celery_app
from app.tasks.system import ping


def test_ping_task_runs_eagerly() -> None:
    celery_app.conf.task_always_eager = True
    result = ping.delay()
    assert result.get() == "pong"
