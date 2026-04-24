#!/bin/bash
cd '/mnt/c/Users/David/OneDrive/Escritorio/Trabajo 2026-1/Plataforma_Unidad_Documentación'

# The issue is that python3 -m venv tries to create symlinks or change permissions on an NTFS mounted drive.
# Instead, we install dependencies system-wide to avoid venv on /mnt/c, using --break-system-packages

python3 -m pip install -r requirements.txt --break-system-packages

python3 manage.py makemigrations core fotografias catalogacion colecciones usuarios || true
python3 manage.py migrate
export DJANGO_SUPERUSER_PASSWORD=admin
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
python3 manage.py createsuperuser --noinput || true
nohup python3 manage.py runserver 0.0.0.0:8000 > django_server.log 2>&1 &
echo "Servidor de Django iniciado!"