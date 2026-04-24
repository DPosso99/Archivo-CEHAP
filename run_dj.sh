#!/bin/bash
cd "/mnt/c/Users/David/OneDrive/Escritorio/Trabajo 2026-1/Plataforma_Unidad_Documentación"
source venv/bin/activate
python manage.py makemigrations core fotografias catalogacion colecciones usuarios || true
python manage.py migrate
export DJANGO_SUPERUSER_PASSWORD=admin
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
python manage.py createsuperuser --noinput || true
nohup python manage.py runserver 0.0.0.0:8000 > django_server.log 2>&1 &
echo "Servidor de Django iniciado!"
