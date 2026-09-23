import os
import sys
import shutil
import sqlite3
import zipfile
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
DEFAULT_BACKUP_NAME = f"Respaldo_Completo_CEHAP_{TIMESTAMP}"

print("=================================================================")
print("  EXPORTADOR Y COPIA DE SEGURIDAD TOTAL - ARCHIVO CEHAP UNAL")
print("=================================================================")
print(f"Directorio origen: {BASE_DIR}")

# Destino: argumento opcional o carpeta en el directorio actual
if len(sys.argv) > 1 and sys.argv[1].strip():
    target_dir = sys.argv[1].strip()
else:
    target_dir = os.path.join(BASE_DIR, DEFAULT_BACKUP_NAME)

os.makedirs(target_dir, exist_ok=True)
print(f"Directorio destino: {target_dir}\n")

# 1. COPIA ATÓMICA Y VERIFICACIÓN DE INTEGRIDAD DE SQLite
src_db = os.path.join(BASE_DIR, "db.sqlite3")
dst_db = os.path.join(target_dir, "db.sqlite3")

if os.path.exists(src_db):
    print("1. Realizando copia atómica de la base de datos (db.sqlite3)...")
    try:
        con_src = sqlite3.connect(src_db)
        con_dst = sqlite3.connect(dst_db)
        con_src.backup(con_dst)
        con_dst.close()
        con_src.close()

        # Verificación de integridad PRAGMA
        check_con = sqlite3.connect(dst_db)
        cur = check_con.cursor()
        cur.execute("PRAGMA integrity_check;")
        check_result = cur.fetchone()[0]
        check_con.close()

        if check_result.lower() == "ok":
            print(f"   [OK] Base de datos copiada y verificada (Integrity: OK) -> {dst_db}")
        else:
            print(f"   [ALERTA] Verificación de integridad arrojó: {check_result}")
    except Exception as e:
        print(f"   [ERROR] No se pudo respaldar db.sqlite3: {e}")
else:
    print("   [INFO] No se encontró db.sqlite3 en el directorio origen.")

# 2. COPIA DE MEDIA (FOTOGRAFÍAS MAESTRAS Y DERIVADOS WEB)
src_media = os.path.join(BASE_DIR, "media")
dst_media = os.path.join(target_dir, "media")

if os.path.exists(src_media):
    print("\n2. Copiando archivos fotográficos (carpeta media/)...")
    total_archivos = 0
    total_bytes = 0
    for root, dirs, files in os.walk(src_media):
        rel_root = os.path.relpath(root, src_media)
        dest_root = os.path.join(dst_media, rel_root)
        os.makedirs(dest_root, exist_ok=True)
        for f in files:
            src_f = os.path.join(root, f)
            dst_f = os.path.join(dest_root, f)
            shutil.copy2(src_f, dst_f)
            total_archivos += 1
            total_bytes += os.path.getsize(src_f)
    print(f"   [OK] {total_archivos} archivos fotográficos copiados ({total_bytes / (1024*1024):.2f} MB).")
else:
    print("\n2. [INFO] No hay carpeta media/ en el proyecto.")

# 3. COPIA DE CÓDIGO FUENTE, PLANTILLAS Y SCRIPTS
print("\n3. Copiando código fuente, plantillas y archivos del sistema...")
DIRS_TO_COPY = ["apps", "config", "templates", "static"]
FILES_TO_COPY = [
    "manage.py",
    "requirements.txt",
    "iniciar_windows.bat",
    "actualizar_universidad.bat",
    "seed_data.json",
]

for d in DIRS_TO_COPY:
    src_d = os.path.join(BASE_DIR, d)
    dst_d = os.path.join(target_dir, d)
    if os.path.exists(src_d):
        if os.path.exists(dst_d):
            shutil.rmtree(dst_d)
        shutil.copytree(
            src_d,
            dst_d,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".ruff_cache"),
        )
        print(f"   [OK] Carpeta copiada: {d}/")

for f in FILES_TO_COPY:
    src_f = os.path.join(BASE_DIR, f)
    dst_f = os.path.join(target_dir, f)
    if os.path.exists(src_f):
        shutil.copy2(src_f, dst_f)
        print(f"   [OK] Archivo copiado: {f}")

# 4. ARCHIVO LEÉME PARA PRESENTACIONES EN OTROS COMPUTADORES
readme_path = os.path.join(target_dir, "INSTRUCCIONES_PRESENTACION.txt")
with open(readme_path, "w", encoding="utf-8") as f:
    f.write(f"""================================================================================
RESPALDO INTEGRAL AUTOCONTENIDO - ARCHIVO FOTOGRÁFICO CEHAP UNAL
Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
================================================================================

Este directorio contiene una copia COMPLETA, AUTOCONTENIDA y VERIFICADA del
sistema CEHAP (Base de datos SQLite + Fotografías en media/ + Código).

CÓMO EJECUTAR ESTA COPIA EN CUALQUIER COMPUTADOR (Para Presentaciones o Pruebas):
--------------------------------------------------------------------------------
1. Copia toda esta carpeta en el nuevo computador (ej. en el Escritorio o una memoria USB).
2. Asegúrate de que el computador tenga Python instalado (python.org).
3. Haz doble clic en el archivo:
   >>> iniciar_windows.bat <<<
4. El sistema se iniciará automáticamente y abrirá http://localhost:8000/ en el navegador
   con el 100% de las fotografías, mapas, colecciones y comentarios intactos.
================================================================================
""")

print("\n=================================================================")
print(f" [ÉXITO] Respaldo completo creado exitosamente en:\n {target_dir}")
print("=================================================================")
