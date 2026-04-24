#!/bin/bash
cd '/mnt/c/Users/David/OneDrive/Escritorio/Trabajo 2026-1/Plataforma_Unidad_Documentación'
rm -rf venv_wsl
python3 -m venv venv_wsl
source venv_wsl/bin/activate
pip install -r requirements.txt
python manage.py makemigrations core fotografias catalogacion colecciones usuarios || true
python manage.py migrate
export DJANGO_SUPERUSER_PASSWORD=admin
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
python manage.py createsuperuser --noinput || true
nohup python manage.py runserver 0.0.0.0:8000 > django_server.log 2>&1 &
echo "Servidor de Django iniciado!"