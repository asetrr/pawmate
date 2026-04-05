import hashlib
import importlib.util
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailVerification

TOKEN_TTL_HOURS = 24


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def create_verification(user):
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    verification, _ = EmailVerification.objects.get_or_create(user=user)
    verification.token_hash = token_hash
    verification.expires_at = timezone.now() + timedelta(hours=TOKEN_TTL_HOURS)
    verification.used_at = None
    verification.save(update_fields=['token_hash', 'expires_at', 'used_at'])
    return raw_token, verification


def send_verification_email(user, request):
    raw_token, _ = create_verification(user)
    verify_path = f"/verify-email/{raw_token}/"
    verify_url = request.build_absolute_uri(verify_path)
    context = {
        'user': user,
        'verify_url': verify_url,
        'expires_hours': TOKEN_TTL_HOURS,
    }
    subject = 'PawMate: подтвердите email'
    message = render_to_string('emails/verify_email.txt', context)

    email_task = None
    if importlib.util.find_spec('celery') is not None:
        try:
            from .tasks import send_email_task
        except ImportError:
            email_task = None
        else:
            email_task = send_email_task

    if email_task is not None and hasattr(email_task, 'delay'):
        email_task.delay(subject, message, [user.email])
    else:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@pawmate.local'),
            [user.email],
            fail_silently=False,
        )


def activate_by_token(raw_token: str):
    token_hash = _hash_token(raw_token)
    verification = (
        EmailVerification.objects.select_related('user')
        .filter(token_hash=token_hash)
        .first()
    )
    if not verification:
        return None, 'invalid'
    if verification.used_at:
        return verification.user, 'already_used'
    if verification.expires_at <= timezone.now():
        return verification.user, 'expired'

    verification.used_at = timezone.now()
    verification.save(update_fields=['used_at'])
    user = verification.user
    user.is_active = True
    user.save(update_fields=['is_active'])
    return user, 'ok'
