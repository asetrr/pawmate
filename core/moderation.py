from datetime import timedelta

from django.utils import timezone

from .models import AbuseReport, UserModerationStatus

MODERATION_REPORT_THRESHOLD = 3
MODERATION_HIDE_DAYS = 7


def is_moderator(user):
    if not user.is_authenticated:
        return False
    return user.is_staff or user.groups.filter(name__iexact='moderators').exists()


def recalc_moderation_status(target_user, latest_reason=''):
    if target_user is None:
        return None
    status, _ = UserModerationStatus.objects.get_or_create(user=target_user)
    valid_reporters_count = (
        AbuseReport.objects.filter(target_user=target_user)
        .exclude(status=AbuseReport.Status.CLOSED)
        .exclude(reporter=target_user)
        .values('reporter_id')
        .distinct()
        .count()
    )
    is_under = valid_reporters_count >= MODERATION_REPORT_THRESHOLD
    hidden_until = timezone.now() + timedelta(days=MODERATION_HIDE_DAYS) if is_under else None
    status.valid_reports_count = valid_reporters_count
    status.is_under_moderation = is_under
    status.hidden_from_swipe_until = hidden_until
    if latest_reason:
        status.last_reason = latest_reason[:220]
    status.save()
    return status
