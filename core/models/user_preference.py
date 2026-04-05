from django.db import models
from .User import User


class UserSwipePreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='swipe_pref')
    species = models.CharField(max_length=64, blank=True)
    city = models.CharField(max_length=64, blank=True)
    min_age = models.PositiveSmallIntegerField(default=0)
    max_age = models.PositiveSmallIntegerField(default=30)
    active_today = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
