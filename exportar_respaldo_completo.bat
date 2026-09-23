@echo off
cd /d "%~dp0"
title Archivo CEHAP - Exportador y Copia de Seguridad Total
color 0A
echo ============================================================
echo   ARCHIVO CEHAP - PLATAFORMA DE DOCUMENTACION
echo   Exportador y Respaldo Total para USB / Presentaciones
echo ============================================================
echo.

:: Verificar Python o venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Entorno virtual activado.
) else (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] No se detecto Python instalado.
        pause
        exit /b 1
    )
    echo [OK] Python detectado en el sistema.
)
echo.

echo Este asistente creara una copia completa e independiente del sistema,
echo incluyendo la base de datos (db.sqlite3), todas las fotografias (media/)
echo y todo el codigo necesario para abrirlo en cualquier otro computador.
echo.
echo Presiona ENTER para guardar en una carpeta en este mismo directorio,
echo o escribe la ruta de tu memoria USB (ejemplo: E:\Respaldo_CEHAP):
echo.
set /p DEST_DIR="Ruta destino [ENTER para predeterminada]: "

if "%DEST_DIR%"=="" (
    python exportar_respaldo.py
) else (
    python exportar_respaldo.py "%DEST_DIR%"
)

echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
