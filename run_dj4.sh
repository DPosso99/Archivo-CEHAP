#!/bin/bash
cd '/mnt/c/Users/David/OneDrive/Escritorio/Trabajo 2026-1/Plataforma_Unidad_Documentación'

# Usa --without-pip para saltar el ensurepip, luego instala pip descargándolo manualmente si es necesario.
# Pero como instalamos python3-venv, DEBERÍA funcionar si le pasamos --system-site-packages?
rm -rf venv_wsl
python3 -m venv --system-site-packages venv_wsl
source venv_wsl/bin/activate

# Forzamos instalación pip en el venv si falta
curl -sS https://bootstrap.pypa.io/get-pip.py | python3
pip install -r requirements.txt

python3 manage.py makemigrations core fotografias catalogacion colecciones usuarios || true
python3 manage.py migrate
export DJANGO_SUPERUSER_PASSWORD=admin
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
python3 manage.py createsuperuser --noinput || true
nohup python3 manage.py runserver 0.0.0.0:8000 > django_server.log 2>&1 &
echo "Servidor de Django iniciado!"