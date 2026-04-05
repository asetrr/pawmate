from django.db import models
from .match import Match
from .User import User


class Message(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.CharField(max_length=400)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
