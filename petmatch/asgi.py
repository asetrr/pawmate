"""
ASGI config for petmatch project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petmatch.settings')

application = get_asgi_application()
