from django.db import models
from .User import User
from .match import Match


class Notification(models.Model):
    class Type(models.TextChoices):
        MATCH = 'match', 'Новый мэтч'
        MESSAGE = 'message', 'Новое сообщение'
        MEETING = 'meeting', 'План встречи'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    kind = models.CharField(max_length=16, choices=Type.choices)
    text = models.CharField(max_length=220)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']