from .models import UserProfileSettings


def site_theme(request):
    theme = 'dark'
    if request.user.is_authenticated:
        value = (
            UserProfileSettings.objects.filter(user=request.user)
            .values_list('theme', flat=True)
            .first()
        )
        if value in {'dark', 'light'}:
            theme = value
    return {'site_theme': theme}
