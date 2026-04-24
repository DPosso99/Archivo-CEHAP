#!/bin/bash
cd '/mnt/c/Users/David/OneDrive/Escritorio/Trabajo 2026-1/Plataforma_Unidad_Documentación'

# To bypass PIP's Externally Managed error and EnsurePIP missing without waiting for apt, use --break-system-packages.
# Or use pipx, or just create venv without pip and download pip into it.
rm -rf venv_wsl
python3 -m venv --without-pip venv_wsl
source venv_wsl/bin/activate
curl -sS https://bootstrap.pypa.io/get-pip.py | python3
python3 -m pip install -r requirements.txt

python3 manage.py makemigrations core fotografias catalogacion colecciones usuarios || true
python3 manage.py migrate
export DJANGO_SUPERUSER_PASSWORD=admin
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
python3 manage.py createsuperuser --noinput || true
nohup python3 manage.py runserver 0.0.0.0:8000 > django_server.log 2>&1 &
echo "Servidor de Django iniciado!"