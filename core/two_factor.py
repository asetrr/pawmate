import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import LoginTwoFactorChallenge

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def _new_code() -> str:
    return f'{secrets.randbelow(1_000_000):06d}'


def send_login_otp(user, request, cooldown_sec: int = 60):
    key = f'auth:2fa:sent:{user.id}'
    if cache.get(key):
        return False

    now = timezone.now()
    LoginTwoFactorChallenge.objects.filter(user=user, used_at__isnull=True).update(used_at=now)
    code = _new_code()
    LoginTwoFactorChallenge.objects.create(
        user=user,
        code_hash=_hash_code(code),
        expires_at=now + timedelta(minutes=OTP_TTL_MINUTES),
    )
    body = render_to_string(
        'emails/login_otp.txt',
        {'user': user, 'code': code, 'minutes': OTP_TTL_MINUTES},
    )
    send_mail(
        'PawMate: код входа',
        body,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'PawMate <no-reply@pawmate.local>'),
        [user.email],
        fail_silently=False,
    )
    cache.set(key, 1, timeout=cooldown_sec)
    return True


def verify_login_otp(user, code: str) -> str:
    challenge = (
        LoginTwoFactorChallenge.objects.filter(user=user, used_at__isnull=True)
        .order_by('-created_at')
        .first()
    )
    if not challenge:
        return 'missing'
    if challenge.expires_at <= timezone.now():
        return 'expired'
    if challenge.attempts >= OTP_MAX_ATTEMPTS:
        return 'locked'
    if challenge.code_hash != _hash_code(code):
        challenge.attempts += 1
        challenge.save(update_fields=['attempts'])
        if challenge.attempts >= OTP_MAX_ATTEMPTS:
            return 'locked'
        return 'invalid'
    challenge.used_at = timezone.now()
    challenge.save(update_fields=['used_at'])
    return 'ok'
