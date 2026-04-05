from django.contrib import admin

from .models import Match, MeetingPlan, Message, Notification, Pet, Swipe, UserSwipePreference, User


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'owner', 'age', 'city', 'created_at')
    list_filter = ('species', 'gender', 'created_at')
    search_fields = ('name', 'owner__username', 'city')


@admin.register(Swipe)
class SwipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'pet', 'liked', 'created_at')
    list_filter = ('liked', 'created_at')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user', 'pet', 'created_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('match', 'sender', 'text', 'created_at')
    search_fields = ('text',)


@admin.register(UserSwipePreference)
class UserSwipePreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'species', 'city', 'min_age', 'max_age', 'updated_at')


@admin.register(MeetingPlan)
class MeetingPlanAdmin(admin.ModelAdmin):
    list_display = ('match', 'place', 'starts_at', 'status', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'text', 'is_read', 'created_at')
    list_filter = ('kind', 'is_read')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email']
