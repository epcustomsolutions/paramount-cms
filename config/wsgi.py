"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Local dev convenience: load environment variables from .env if present.
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Vercel Python runtime expects a WSGI callable named `app`.
app = application
