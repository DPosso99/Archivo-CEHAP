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

:: Copy .env.example if .env doesn't exist
if not exist ".env" (
    echo Creando archivo .env desde .env.example...
    copy .env.example .env >nul
    echo [OK] .env creado. Editalo si necesitas cambiar las claves.
)
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

:: Use SQLite for Windows (no PostgreSQL needed)
set DJANGO_SETTINGS_MODULE=config.settings.local_windows

:: Install requirements
echo Instalando dependencias...
pip install -r requirements.txt --quiet
echo [OK] Dependencias instaladas.
echo.

:: Run migrations
echo Preparando base de datos...
if exist "db.sqlite3" del /q "db.sqlite3"
python manage.py migrate --noinput
if %errorlevel% neq 0 (
    echo [ERROR] Fallaron las migraciones. Revisa los errores arriba.
    pause
    exit /b 1
)
echo [OK] Base de datos lista.
echo.

:: Create admin user if needed
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.filter(username='admin').first(); exit(0) if u else User.objects.create_superuser('admin','admin@localhost','admin')"
echo [OK] Usuario listo (admin / admin).
echo.

:: Collect static files
python manage.py collectstatic --noinput
echo [OK] Archivos estaticos listos.
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
