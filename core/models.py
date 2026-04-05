from django.conf import settings
from django.db import models


class Pet(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'Самец'
        FEMALE = 'female', 'Самка'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=64)
    species = models.CharField(max_length=64)
    breed = models.CharField(max_length=64, blank=True)
    age = models.PositiveSmallIntegerField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    city = models.CharField(max_length=64, blank=True)
    bio = models.TextField(max_length=500)
    photo = models.ImageField(upload_to='pets/', blank=True)
    photo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.owner.username})'

    @property
    def display_photo(self):
        if self.photo:
            return self.photo.url
        return self.photo_url


class Swipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='swipes')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='swipes')
    liked = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pet')
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['pet', 'created_at']),
        ]


class Match(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='matches')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pet')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['pet', '-created_at']),
        ]


class Message(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.CharField(max_length=400)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['match', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]


class UserSwipePreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='swipe_pref')
    species = models.CharField(max_length=64, blank=True)
    city = models.CharField(max_length=64, blank=True)
    min_age = models.PositiveSmallIntegerField(default=0)
    max_age = models.PositiveSmallIntegerField(default=30)
    active_today = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class UserProfileSettings(models.Model):
    class Theme(models.TextChoices):
        DARK = 'dark', 'Темная'
        LIGHT = 'light', 'Светлая'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile_settings')
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.DARK)
    two_factor_enabled = models.BooleanField(default=False)
    show_demo_profiles = models.BooleanField(default=True)
    show_swipe_hotkeys = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


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


class Notification(models.Model):
    class Type(models.TextChoices):
        MATCH = 'match', 'Новый мэтч'
        MESSAGE = 'message', 'Новое сообщение'
        MEETING = 'meeting', 'План встречи'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    kind = models.CharField(max_length=16, choices=Type.choices)
    text = models.CharField(max_length=220)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class UserBlock(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocks')
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blocked_user')


class AbuseReport(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Открыт'
        REVIEWED = 'reviewed', 'Проверен'
        CLOSED = 'closed', 'Закрыт'

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_about_me',
        null=True,
        blank=True,
    )
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reason = models.CharField(max_length=220)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class UserModerationStatus(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='moderation_status')
    valid_reports_count = models.PositiveIntegerField(default=0)
    is_under_moderation = models.BooleanField(default=False)
    hidden_from_swipe_until = models.DateTimeField(null=True, blank=True)
    last_reason = models.CharField(max_length=220, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Статус модерации'
        verbose_name_plural = 'Статусы модерации'


class ModerationAppeal(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Открыта'
        REVIEWED = 'reviewed', 'Рассмотрена'
        REJECTED = 'rejected', 'Отклонена'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='moderation_appeals')
    text = models.CharField(max_length=500)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    moderator_note = models.CharField(max_length=220, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_verification')
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class LoginTwoFactorChallenge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='login_2fa_challenges')
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
