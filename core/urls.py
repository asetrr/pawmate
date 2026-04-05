from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('healthz/', views.healthz, name='healthz'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('safety/', views.safety, name='safety'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('community-rules/', views.community_rules, name='community_rules'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.txt',
            subject_template_name='registration/password_reset_subject.txt',
            success_url='/password-reset/done/',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url='/reset/done/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
        name='password_reset_complete',
    ),
    path('login/2fa/', views.login_2fa_view, name='login_2fa'),
    path('login/2fa/resend/', views.login_2fa_resend_view, name='login_2fa_resend'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('resend-verification-email/', views.resend_verification_email_view, name='resend_verification_email'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notifications/', views.notifications_history, name='notifications_history'),
    path('settings/', views.profile_settings_view, name='profile_settings'),
    path('settings/delete-account/', views.delete_account_view, name='delete_account'),
    path('moderation/', views.moderation_center, name='moderation'),
    path('moderation/queue/', views.moderation_queue, name='moderation_queue'),
    path('my-restrictions/', views.my_restrictions, name='my_restrictions'),
    path('my-restrictions/appeal/', views.submit_moderation_appeal, name='submit_moderation_appeal'),
    path('pets/new/', views.pet_create, name='pet_create'),
    path('pets/<int:pet_id>/edit/', views.pet_edit, name='pet_edit'),
    path('swipe/', views.swipe_view, name='swipe'),
    path('api/swipe/<int:pet_id>/', views.swipe_api, name='swipe_api'),
    path('api/pets/<int:pet_id>/report/', views.report_pet_api, name='report_pet_api'),
    path('api/messages/<int:message_id>/report/', views.report_message_api, name='report_message_api'),
    path('api/pets/<int:pet_id>/block/', views.block_pet_owner_api, name='block_pet_owner_api'),
    path('api/users/<int:user_id>/unblock/', views.unblock_user_api, name='unblock_user_api'),
    path('api/moderation/reports/<int:report_id>/action/', views.moderation_report_action_api, name='moderation_report_action_api'),
    path('chats/', views.chats, name='chats'),
    path('api/chats/<int:match_id>/send/', views.send_message_api, name='send_message_api'),
    path('api/chats/<int:match_id>/messages/', views.fetch_messages_api, name='fetch_messages_api'),
    path('api/chats/<int:match_id>/meeting/', views.update_meeting_api, name='update_meeting_api'),
    path('api/chats/<int:match_id>/meeting/confirm/', views.confirm_meeting_api, name='confirm_meeting_api'),
]
