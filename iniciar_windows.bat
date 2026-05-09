@echo off
title Archivo CEHAP - Plataforma de Documentacion
color 0A
echo ============================================
echo  Archivo CEHAP - Galeria de Imagenes
echo  Escuela del Habitat - UNAL Medellin
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado.
    echo Descargalo desde https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

echo [OK] Python detectado.
echo.

:: Setup virtual environment if not exists
if not exist "venv\" (
    echo Creando entorno virtual...
    python -m venv venv
    echo [OK] Entorno virtual creado.
) else (
    echo [OK] Entorno virtual existente.
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install requirements
echo Instalando dependencias...
pip install -r requirements.txt --quiet
echo [OK] Dependencias instaladas.
echo.

:: Run migrations
echo Preparando base de datos...
python manage.py migrate --noinput
echo [OK] Base de datos lista.
echo.

:: Create admin user if needed
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.filter(username='admin').first(); exit(0) if u else User.objects.create_superuser('admin','admin@localhost','admin')"
echo [OK] Usuario listo (admin / admin).
echo.

:: Start server and open browser
echo ============================================
echo  Iniciando servidor...
echo  Abriendo http://localhost:8000/
echo  Usuario: admin / Contrasena: admin
echo  Presiona Ctrl+C para detener el servidor
echo ============================================
start http://localhost:8000/
python manage.py runserver 0.0.0.0:8000
pause
