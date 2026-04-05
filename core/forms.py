from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import MeetingPlan, Message, Pet, UserSwipePreference


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['name', 'species', 'breed', 'age', 'gender', 'city', 'photo_url', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']


class SwipePreferenceForm(forms.ModelForm):
    class Meta:
        model = UserSwipePreference
        fields = ['species', 'city', 'min_age', 'max_age', 'active_today']


class MeetingPlanForm(forms.ModelForm):
    starts_at = forms.DateTimeField(
        required=False,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )

    class Meta:
        model = MeetingPlan
        fields = ['place', 'starts_at', 'status', 'note']
