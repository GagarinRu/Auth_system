#!/usr/bin/env bash
set -e

echo "Применение миграций"
python3 manage.py migrate --noinput

echo "Инициализация RBAC"
python3 manage.py init_rbac

echo "Старт Gunicorn"
exec gunicorn config.wsgi:application \
    --bind "${APP_GUVICORN_HOST}:${APP_GUVICORN_PORT}" \
    --workers 3 \
    --timeout 120 \
    --preload
