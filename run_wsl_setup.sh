#!/bin/bash
set -e

echo ">>> Instalando PostgreSQL en WSL..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

echo ">>> Iniciando servicio PostgreSQL..."
sudo service postgresql start
sudo service postgresql status

echo ">>> Configurando Base de Datos y Usuario..."
sudo -u postgres psql -c "CREATE DATABASE documental_cehap;" || true
sudo -u postgres psql -c "CREATE USER documental_user WITH PASSWORD 'documental2026';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE documental_cehap TO documental_user;"
sudo -u postgres psql -c "ALTER DATABASE documental_cehap OWNER TO documental_user;"

echo ">>> Navegando al proyecto y configurando entorno Python..."
cd "/mnt/c/Users/David/OneDrive/Escritorio/Trabajo 2026-1/Plataforma_Unidad_Documentación"
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo ">>> Ejecutando migraciones..."
python manage.py migrate

echo ">>> Creando superusuario (admin / admin)..."
export DJANGO_SUPERUSER_PASSWORD=admin
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
python manage.py createsuperuser --noinput || true

echo ">>> Iniciando servidor en segundo plano..."
nohup python manage.py runserver 0.0.0.0:8000 > django_server.log 2>&1 &
echo "Servidor Django corriendo en http://localhost:8000"