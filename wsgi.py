"""
Vercel WSGI entrypoint.

The Python runtime discovers ``wsgi.py`` at the repository root; Django lives under
``config/wsgi.py``. Import the callable Vercel expects (``app``).
"""

from config.wsgi import app  # noqa: F401
