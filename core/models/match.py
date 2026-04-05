from django.db import models
from .pet import Pet
from .User import User


class Match(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='matches')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pet')
        ordering = ['-created_at']
