from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

from .models import MeetingPlan, Message, Pet, UserSwipePreference


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите логин'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Придумайте пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })

        self.fields['username'].hepl_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None


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
