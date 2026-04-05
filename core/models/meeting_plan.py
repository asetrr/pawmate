from django.db import models
from .match import Match


class MeetingPlan(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PROPOSED = 'proposed', 'Предложено'
        CONFIRMED = 'confirmed', 'Подтверждено'
        DONE = 'done', 'Завершено'

    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='meeting_plan')
    place = models.CharField(max_length=120, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=220, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    confirmed_by_user = models.BooleanField(default=False)
    confirmed_by_owner = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

