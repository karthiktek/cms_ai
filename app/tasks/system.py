from celery import shared_task


@shared_task(name="app.tasks.system.ping")  # type: ignore[untyped-decorator]
def ping() -> str:
    return "pong"
