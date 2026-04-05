from pathlib import Path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

BASE_DIR = Path(__file__).resolve().parent.parent

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path(
        'sitemap.xml',
        lambda request: HttpResponse(
            open(BASE_DIR / 'templates' / 'sitemap.xml', encoding='utf-8').read(),
            content_type='application/xml',
        ),
    ),
    path(
        'robots.txt',
        lambda request: HttpResponse(
            open(BASE_DIR / 'templates' / 'robots.txt', encoding='utf-8').read(),
            content_type='text/plain',
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
