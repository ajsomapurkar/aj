import os
from celery import Celery

# Configure Celery broker from env (Redis recommended)
celery = Celery('ambit_tasks', broker=os.getenv(
    'CELERY_BROKER_URL', 'redis://localhost:6379/0'))


@celery.task(bind=True, max_retries=3)
def send_email_task(self, to_email, subject, body):
    try:
        # import here to avoid circular imports at module import time
        from mailer import send_email
        ok = send_email(to_email, subject, body)
        if not ok:
            raise Exception('send failed')
        return True
    except Exception as exc:
        try:
            self.retry(exc=exc, countdown=2 ** self.request.retries)
        except Exception:
            return False
