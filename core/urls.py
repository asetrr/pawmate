from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('safety/', views.safety, name='safety'),
    path('faq/', views.faq, name='faq'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pets/new/', views.pet_create, name='pet_create'),
    path('pets/<int:pet_id>/edit/', views.pet_edit, name='pet_edit'),
    path('swipe/', views.swipe_view, name='swipe'),
    path('api/swipe/<int:pet_id>/', views.swipe_api, name='swipe_api'),
    path('chats/', views.chats, name='chats'),
    path('api/chats/<int:match_id>/send/', views.send_message_api, name='send_message_api'),
    path('api/chats/<int:match_id>/meeting/', views.update_meeting_api, name='update_meeting_api'),
    path('api/chats/<int:match_id>/meeting/confirm/', views.confirm_meeting_api, name='confirm_meeting_api'),
]
