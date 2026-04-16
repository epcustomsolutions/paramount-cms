#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Match production STATIC_ROOT on Vercel (see config/settings.py).
if [ -n "${VERCEL:-}" ]; then
  export DJANGO_STATIC_ROOT="static_deploy"
fi

python3 manage.py collectstatic --noinput

# Mirror collected assets into public/ so the edge can serve /static/* before the WSGI catch-all.
if [ -n "${VERCEL:-}" ]; then
  rm -rf public/static
  mkdir -p public/static
  cp -a static_deploy/. public/static/
fi
