import importlib
from django.conf import settings
from django.core.mail import send_mail

if importlib.util.find_spec('celery') is not None:
    from celery import shared_task

    @shared_task(bind=True)
    def send_email_task(self, subject: str, message: str, recipient_list: list[str]) -> bool:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@pawmate.local'),
            recipient_list,
            fail_silently=False,
        )
        return True
