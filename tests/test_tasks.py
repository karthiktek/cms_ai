from app.tasks.celery_app import celery_app


def test_ping_task_runs_eagerly() -> None:
    celery_app.loader.import_default_modules()
    celery_app.conf.task_always_eager = True
    ping = celery_app.tasks["app.tasks.system.ping"]
    result = ping.delay()
    assert result.get() == "pong"
