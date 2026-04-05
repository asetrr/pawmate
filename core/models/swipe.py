from django.db import models
from .pet import Pet


class Swipe(models.Model):
    user = models.ForeignKey(to='User', on_delete=models.CASCADE, related_name='swipes')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='swipes')
    liked = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pet')
