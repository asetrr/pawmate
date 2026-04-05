from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import MeetingPlan, Message, ModerationAppeal, Pet, UserProfileSettings, UserSwipePreference

MAX_PET_PHOTO_BYTES = 6 * 1024 * 1024
ALLOWED_PET_PHOTO_TYPES = {'image/jpeg', 'image/png', 'image/webp'}


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    accept_terms = forms.BooleanField(
        required=True,
        label='Я принимаю условия использования и политику конфиденциальности',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'accept_terms')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, initial=False, label='Запомнить меня')


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['name', 'species', 'breed', 'age', 'gender', 'city', 'photo', 'photo_url', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo

        if getattr(photo, 'size', 0) > MAX_PET_PHOTO_BYTES:
            raise forms.ValidationError('Фото слишком большое. Максимум 6 МБ.')

        content_type = (getattr(photo, 'content_type', '') or '').lower()
        if content_type and content_type not in ALLOWED_PET_PHOTO_TYPES:
            raise forms.ValidationError('Поддерживаются только JPG, PNG или WEBP.')
        return photo

    def clean(self):
        cleaned_data = super().clean()
        photo = cleaned_data.get('photo') or getattr(self.instance, 'photo', None)
        photo_url = cleaned_data.get('photo_url') or getattr(self.instance, 'photo_url', '')
        if not photo and not photo_url:
            raise forms.ValidationError('Добавь фото питомца: загрузи файл или укажи URL.')
        return cleaned_data


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']


class SwipePreferenceForm(forms.ModelForm):
    class Meta:
        model = UserSwipePreference
        fields = ['species', 'city', 'min_age', 'max_age', 'active_today']


class ProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfileSettings
        fields = ['theme', 'two_factor_enabled', 'show_demo_profiles', 'show_swipe_hotkeys']
        widgets = {
            'theme': forms.RadioSelect,
        }


class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    confirm = forms.BooleanField(
        required=True,
        label='Я понимаю, что удаление аккаунта необратимо',
    )


class ModerationAppealForm(forms.ModelForm):
    class Meta:
        model = ModerationAppeal
        fields = ['text']
        widgets = {
            'text': forms.Textarea(
                attrs={
                    'rows': 4,
                    'maxlength': 500,
                    'placeholder': 'Опиши, почему ты считаешь ограничение ошибочным.',
                }
            ),
        }


class MeetingPlanForm(forms.ModelForm):
    starts_at = forms.DateTimeField(
        required=False,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )

    class Meta:
        model = MeetingPlan
        fields = ['place', 'starts_at', 'status', 'note']
