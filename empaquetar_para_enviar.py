import os
import sys
import shutil
import sqlite3
import zipfile
import tempfile
import subprocess
from datetime import datetime

# Asegurar codificacion UTF-8 en consola de Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("==================================================================")
print("  ARCHIVO CEHAP - RESPALDO DE FOTOGRAFIAS Y METADATOS")
print("  Universidad Nacional de Colombia - Sede Medellin")
print("==================================================================")
print()

# ----------------------------------------------------------------------
# 1. LOCALIZAR LA CARPETA PRINCIPAL DEL PROYECTO
# ----------------------------------------------------------------------
base_dir = None

# Prioridad 1: argumento pasado por linea de comandos
if len(sys.argv) > 1 and sys.argv[1].strip():
    cand = sys.argv[1].strip().strip('"').strip("'")
    if os.path.isdir(cand) and (os.path.exists(os.path.join(cand, "manage.py")) or os.path.exists(os.path.join(cand, "db.sqlite3"))):
        base_dir = os.path.abspath(cand)

# Prioridad 2: carpeta actual donde reside este script
if not base_dir:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, "manage.py")) or os.path.exists(os.path.join(script_dir, "db.sqlite3")):
        base_dir = script_dir

# Prioridad 3: directorio actual de trabajo
if not base_dir:
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "manage.py")) or os.path.exists(os.path.join(cwd, "db.sqlite3")):
        base_dir = cwd

# Prioridad 4: ubicaciones comunes en Windows
if not base_dir:
    user_home = os.path.expanduser("~")
    rutas_comunes = [
        os.path.join(user_home, "Desktop", "Plataforma_Unidad_Documentacion"),
        os.path.join(user_home, "Escritorio", "Plataforma_Unidad_Documentacion"),
        os.path.join(user_home, "Desktop", "Plataforma_Unidad_Documentación"),
        os.path.join(user_home, "Escritorio", "Plataforma_Unidad_Documentación"),
        os.path.join(user_home, "Desktop", "Archivo-CEHAP"),
        os.path.join(user_home, "Escritorio", "Archivo-CEHAP"),
        r"C:\Plataforma_Unidad_Documentación",
        r"C:\Plataforma_Unidad_Documentacion",
        r"C:\Archivo-CEHAP",
    ]
    for r in rutas_comunes:
        if os.path.isdir(r) and (os.path.exists(os.path.join(r, "manage.py")) or os.path.exists(os.path.join(r, "db.sqlite3"))):
            base_dir = r
            break

if not base_dir or not os.path.exists(base_dir):
    print("[ERROR] No se pudo encontrar la carpeta principal del proyecto.")
    print("Por favor copia y ejecuta este archivo dentro de la carpeta")
    print("'Plataforma_Unidad_Documentacion' donde se encuentran 'manage.py' y 'db.sqlite3'.")
    print()
    sys.exit(1)

print(f"Directorio del proyecto detectado:\n  -> {base_dir}\n")

# ----------------------------------------------------------------------
# 2. LOCALIZAR EL ESCRITORIO DE WINDOWS
# ----------------------------------------------------------------------
desktop_dir = None
try:
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
    raw_path, _ = winreg.QueryValueEx(key, "Desktop")
    winreg.CloseKey(key)
    cand_desktop = os.path.expandvars(raw_path)
    if os.path.exists(cand_desktop):
        desktop_dir = cand_desktop
except Exception:
    pass

if not desktop_dir or not os.path.exists(desktop_dir):
    user_home = os.path.expanduser("~")
    for cand in [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Escritorio"),
        os.path.join(user_home, "OneDrive", "Desktop"),
        os.path.join(user_home, "OneDrive", "Escritorio"),
    ]:
        if os.path.exists(cand):
            desktop_dir = cand
            break

if not desktop_dir or not os.path.exists(desktop_dir):
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(desktop_dir, exist_ok=True)

timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
zip_filename = f"Respaldo_CEHAP_UNAL_{timestamp_str}.zip"
zip_filepath = os.path.join(desktop_dir, zip_filename)

print(f"Destino del archivo ZIP:\n  -> {zip_filepath}\n")

# ----------------------------------------------------------------------
# 3. PREPARAR CARPETA TEMPORAL Y COPIA ATOMICA DE LA BASE DE DATOS
# ----------------------------------------------------------------------
temp_dir = tempfile.mkdtemp(prefix="cehap_empaquetar_")
temp_db = os.path.join(temp_dir, "db.sqlite3")
src_db = os.path.join(base_dir, "db.sqlite3")

db_respaldada = False
if os.path.exists(src_db):
    print("[1/3] Respaldando base de datos de catalogaciones (db.sqlite3)...")
    try:
        # Copia atomica online para SQLite (segura incluso si Django esta en ejecucion)
        con_src = sqlite3.connect(src_db)
        con_dst = sqlite3.connect(temp_db)
        con_src.backup(con_dst)
        con_dst.close()
        con_src.close()

        # Verificacion de integridad
        check_con = sqlite3.connect(temp_db)
        cur = check_con.cursor()
        cur.execute("PRAGMA integrity_check;")
        check_res = cur.fetchone()[0]
        check_con.close()

        if check_res.lower() == "ok":
            print("      Base de datos SQLite respaldada y verificada (Integridad: OK).")
            db_respaldada = True
        else:
            print(f"      [AVISO] Verificacion de integridad SQLite: {check_res}")
            db_respaldada = True
    except Exception as e:
        print(f"      [AVISO] Copia atomica fallo ({e}), realizando copia directa...")
        try:
            shutil.copy2(src_db, temp_db)
            db_respaldada = True
            print("      Base de datos SQLite copiada directamente.")
        except Exception as e2:
            print(f"      [ERROR] No se pudo copiar db.sqlite3: {e2}")
else:
    print("[1/3] [AVISO] No se encontro db.sqlite3 en el directorio del proyecto.")

# Intentar volcado JSON de metadatos con Django dumpdata si esta disponible
json_dump_path = os.path.join(temp_dir, "metadatos_cehap.json")
manage_py = os.path.join(base_dir, "manage.py")
if os.path.exists(manage_py):
    try:
        print("      Generando volcado de metadatos en formato JSON...")
        res = subprocess.run(
            [sys.executable, manage_py, "dumpdata", "fotografias", "colecciones", "--indent", "2", "-o", json_dump_path],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=45
        )
        if res.returncode == 0 and os.path.exists(json_dump_path) and os.path.getsize(json_dump_path) > 0:
            print("      Metadatos exportados exitosamente a JSON (metadatos_cehap.json).")
    except Exception:
        pass

# ----------------------------------------------------------------------
# 4. RECOLECTAR ARCHIVOS FOTOGRAFICOS (CARPETA MEDIA)
# ----------------------------------------------------------------------
src_media = os.path.join(base_dir, "media")
archivos_media = []

if os.path.exists(src_media):
    print("\n[2/3] Escaneando fotografias y archivos multimedia...")
    for root, dirs, files in os.walk(src_media):
        for f in files:
            # Omitir archivos temporales de Windows o flujos de metadatos
            if ":Zone.Identifier" in f or f in ("Thumbs.db", ".DS_Store"):
                continue
            abs_p = os.path.join(root, f)
            rel_p = os.path.relpath(abs_p, base_dir)
            archivos_media.append((abs_p, rel_p))

    total_bytes_media = sum(os.path.getsize(p[0]) for p in archivos_media)
    print(f"      Total de archivos multimedia detectados: {len(archivos_media)} ({total_bytes_media / (1024 * 1024):.2f} MB)")
else:
    print("\n[2/3] [AVISO] No se encontro la carpeta media/ en el proyecto.")

# ----------------------------------------------------------------------
# 5. CREAR ARCHIVO ZIP CON COMPRESION
# ----------------------------------------------------------------------
print(f"\n[3/3] Comprimiendo paquete en el Escritorio...")
print(f"      Archivo: {zip_filename}")

total_empaquetados = 0
with zipfile.ZipFile(zip_filepath, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
    # A. Agregar base de datos SQLite
    if db_respaldada and os.path.exists(temp_db):
        zipf.write(temp_db, "db.sqlite3")
        total_empaquetados += 1

    # B. Agregar volcado JSON si existe
    if os.path.exists(json_dump_path):
        zipf.write(json_dump_path, "metadatos_cehap.json")
        total_empaquetados += 1

    # C. Agregar .env si existe en el proyecto
    env_file = os.path.join(base_dir, ".env")
    if os.path.exists(env_file):
        zipf.write(env_file, ".env")
        total_empaquetados += 1

    # D. Agregar todas las fotografias y medios
    total_fotos = len(archivos_media)
    for idx, (abs_p, rel_p) in enumerate(archivos_media, 1):
        zipf.write(abs_p, rel_p)
        total_empaquetados += 1
        if idx % 20 == 0 or idx == total_fotos:
            porcentaje = int((idx / total_fotos) * 100)
            print(f"      Progreso: {idx}/{total_fotos} fotos comprimidas ({porcentaje}%)...")

    # E. Archivo informativo del respaldo
    info_content = f"""================================================================================
INFORMACION DEL RESPALDO - ARCHIVO CEHAP UNAL
================================================================================
Fecha de generacion : {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Equipo origen       : {os.environ.get("COMPUTERNAME", "Desconocido")}
Usuario Windows     : {os.environ.get("USERNAME", "Desconocido")}
Directorio origen   : {base_dir}

CONTENIDO DEL PAQUETE:
- db.sqlite3            : Base de datos SQLite completa (catalogaciones, usuarios, colecciones).
- metadatos_cehap.json  : Volcado portable de metadatos en formato JSON.
- media/                : Todas las fotografias maestras originales y derivadas web.
- .env                  : Configuracion y variables de entorno del equipo (si aplica).

Total archivos incluidos: {total_empaquetados}
================================================================================
"""
    zipf.writestr("INFORMACION_RESPALDO.txt", info_content)
    total_empaquetados += 1

# ----------------------------------------------------------------------
# 6. LIMPIEZA DE TEMPORALES Y REPORTE FINAL
# ----------------------------------------------------------------------
try:
    shutil.rmtree(temp_dir, ignore_errors=True)
except Exception:
    pass

zip_mb = os.path.getsize(zip_filepath) / (1024 * 1024)

print()
print("==================================================================")
print("  RESPALDO GENERADO CON EXITO")
print("==================================================================")
print(f"Ubicacion del archivo ZIP:")
print(f"  -> {zip_filepath}")
print()
print(f"Detalles:")
print(f"  - Total archivos incluidos : {total_empaquetados}")
print(f"  - Tamano del archivo ZIP   : {zip_mb:.2f} MB")
print()
print("QUE DEBES HACER AHORA:")
print("  1. Envia este archivo .zip a David Julian Taimal Poso.")
print("  2. Puedes enviarlo por Google Drive, correo electronico o una memoria USB.")
print("==================================================================")

# Abrir el Explorador de Windows con el archivo seleccionado
try:
    subprocess.Popen(f'explorer.exe /select,"{zip_filepath}"')
except Exception:
    pass
