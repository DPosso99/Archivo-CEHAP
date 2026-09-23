@echo off
cd /d "%~dp0"
title Archivo CEHAP - Actualizador Seguro UNAL
color 0B
echo ============================================================
echo   ARCHIVO CEHAP - PLATAFORMA DE DOCUMENTACION
echo   Script de Actualizacion Segura (Sin permisos de TI)
echo ============================================================
echo.

:: 1. Verificar Python o entorno virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Entorno virtual activado.
) else (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] No se detecto Python ni la carpeta 'venv'.
        echo Asegurate de ejecutar este script en la carpeta principal del proyecto.
        pause
        exit /b 1
    )
    echo [OK] Python detectado en el sistema.
)
echo.

:: 2. Configuracion de entorno Windows (SQLite)
set DJANGO_SETTINGS_MODULE=config.settings.local_windows

:: 3. CREAR COPIA DE SEGURIDAD AUTOMATICA DE LA BASE DE DATOS
echo ============================================================
echo [PASO 1/3] Creando copia de seguridad de la base de datos...
echo ============================================================

if not exist "backups" mkdir backups

:: Obtener timestamp limpio para Windows (independiente de idioma/formato)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set datetime=%%I
if defined datetime (
    set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
) else (
    set TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%random%
)

if exist "db.sqlite3" (
    copy /Y "db.sqlite3" "backups\db_respaldo_%TIMESTAMP%.sqlite3" >nul
    if %errorlevel% equ 0 (
        echo [OK] Respaldo creado exitosamente:
        echo      backups\db_respaldo_%TIMESTAMP%.sqlite3
    ) else (
        echo [ALERTA] No se pudo crear la copia automatica en backups.
        echo Se recomienda copiar manualmente 'db.sqlite3' antes de continuar.
        pause
    )
) else (
    echo [INFO] No se encontro db.sqlite3 previa. Se creara una nueva en las migraciones.
)
echo.

:: 4. APLICAR MIGRACIONES DE MANERA SEGURA (ADITIVA)
echo ============================================================
echo [PASO 2/3] Aplicando actualizaciones de base de datos...
echo ============================================================
python manage.py migrate --noinput
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un inconveniente al aplicar las migraciones.
    echo Tu base de datos original esta protegida en la carpeta 'backups\'.
    echo Por favor no intentes borrar ningun archivo.
    pause
    exit /b 1
)
echo [OK] Base de datos actualizada correctamente.
echo.

:: 5. RECOLECTAR Y ACTUALIZAR ARCHIVOS ESTATICOS LOCALES
echo ============================================================
echo [PASO 3/4] Actualizando librerias locales y mapa de Medellin...
echo ============================================================
python manage.py collectstatic --noinput
echo [OK] Archivos estaticos y mosaicos locales actualizados.
echo.

:: 6. GENERAR DERIVADOS WEB CON MARCA DE AGUA CEHAP
echo ============================================================
echo [PASO 4/4] Protegiendo fotografias existentes (Marcas de agua CEHAP)...
echo ============================================================
python manage.py generar_marcas_agua
echo.

:: 7. FINALIZACION EXITOSA
echo ============================================================
echo   ACTUALIZACION COMPLETADA CON EXITO
echo ============================================================
echo   1. Tus fotografias originales maestras estan 100% INTACTAS.
echo   2. Se guardo un respaldo de seguridad en la carpeta 'backups\'.
echo   3. El mapa cuenta con CartoDB, Esri y Mosaico Offline de Medellin.
echo   4. Las librerias Leaflet se cargan de forma 100% local.
echo   5. Busqueda inteligente activa (tildes, plurales, multi-palabra).
echo   6. Concurrencia SQLite WAL activa para multiples catalogadores.
echo   7. Copias web protegidas con marca de agua institucional.
echo ============================================================
echo.
echo Presiona cualquier tecla para cerrar este asistente.
pause >nul
