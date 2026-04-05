from django.db import models
from .User import User

class Pet(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'Самец'
        FEMALE = 'female', 'Самка'

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=64)
    species = models.CharField(max_length=64)
    breed = models.CharField(max_length=64, blank=True)
    age = models.PositiveSmallIntegerField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    city = models.CharField(max_length=64, blank=True)
    bio = models.TextField(max_length=500)
    photo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.owner.username})'
