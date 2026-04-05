from django.contrib import admin

from .moderation import recalc_moderation_status

from .models import (
    AbuseReport,
    EmailVerification,
    LoginTwoFactorChallenge,
    Match,
    MeetingPlan,
    Message,
    ModerationAppeal,
    Notification,
    Pet,
    Swipe,
    UserBlock,
    UserModerationStatus,
    UserProfileSettings,
    UserSwipePreference,
)


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


@admin.register(UserProfileSettings)
class UserProfileSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'two_factor_enabled', 'show_demo_profiles', 'show_swipe_hotkeys', 'updated_at')
    list_filter = ('theme', 'two_factor_enabled', 'show_demo_profiles', 'show_swipe_hotkeys')


@admin.register(MeetingPlan)
class MeetingPlanAdmin(admin.ModelAdmin):
    list_display = ('match', 'place', 'starts_at', 'status', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'text', 'is_read', 'created_at')
    list_filter = ('kind', 'is_read')


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ('user', 'blocked_user', 'created_at')


@admin.register(AbuseReport)
class AbuseReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'target_user', 'pet', 'match', 'message', 'reason', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('reason', 'reporter__username', 'target_user__username')
    actions = ['mark_reviewed', 'mark_closed']

    def _recalc_for_reports(self, reports):
        target_users = {r.target_user for r in reports if r.target_user_id}
        for user in target_users:
            recalc_moderation_status(user)

    @admin.action(description='Отметить как проверенные')
    def mark_reviewed(self, request, queryset):
        queryset.update(status=AbuseReport.Status.REVIEWED)
        self._recalc_for_reports(list(queryset))

    @admin.action(description='Закрыть жалобы')
    def mark_closed(self, request, queryset):
        queryset.update(status=AbuseReport.Status.CLOSED)
        self._recalc_for_reports(list(queryset))

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        recalc_moderation_status(obj.target_user)

    def delete_model(self, request, obj):
        target_user = obj.target_user
        super().delete_model(request, obj)
        recalc_moderation_status(target_user)

    def delete_queryset(self, request, queryset):
        target_users = list({r.target_user for r in queryset if r.target_user_id})
        super().delete_queryset(request, queryset)
        for user in target_users:
            recalc_moderation_status(user)


@admin.register(UserModerationStatus)
class UserModerationStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'valid_reports_count', 'is_under_moderation', 'hidden_from_swipe_until', 'updated_at')
    list_filter = ('is_under_moderation',)
    search_fields = ('user__username', 'last_reason')


@admin.register(ModerationAppeal)
class ModerationAppealAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'text', 'moderator_note')


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires_at', 'used_at', 'created_at')
    search_fields = ('user__username', 'user__email')


@admin.register(LoginTwoFactorChallenge)
class LoginTwoFactorChallengeAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires_at', 'used_at', 'attempts', 'created_at')
    search_fields = ('user__username', 'user__email')


