# Plataforma de la Unidad de Documentación — Archivo Fotográfico CEHAP

[![Django](https://img.shields.io/badge/Django-5.0+-092e20?style=flat&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)](https://www.python.org/)
[![Database](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57?style=flat&logo=sqlite)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/Institución-Universidad%20Nacional%20de%20Colombia-008000?style=flat)](https://unal.edu.co/)

Sistema web para la catalogación, georreferenciación, preservación digital y divulgación del acervo fotográfico y documental de la **Escuela del Hábitat (CEHAP)**, perteneciente a la **Facultad de Arquitectura de la Universidad Nacional de Colombia (Sede Medellín)**.

---

## Contexto del Proyecto

El archivo del CEHAP alberga décadas de investigación y registro visual sobre arquitectura popular, procesos de hábitat, transformaciones urbanas en Medellín y el territorio colombiano. 

Esta plataforma permite a investigadores, docentes y catalogadores registrar metadatos detallados de cada fotografía, ubicar espacialmente los registros en mapas históricos y contemporáneos, y proteger el patrimonio documental mediante copias web con marcas de agua institucionales, preservando siempre el archivo maestro original intacto.

---

## Características Principales

* **Motor de Búsqueda Inteligente:** Búsqueda insensible a acentos/tildes (`medellin` encuentra `Medellín`), soporte multi-palabra con operador `AND` y lematización básica de plurales y singulares.
* **Georreferenciación y Mapas Híbridos:** 
  * Integración con **CartoDB Voyager** y **Esri Satelital**.
  * **Librerías Leaflet 100% locales** (cero dependencias de CDNs externas).
  * **Mosaico Local Offline de Medellín y Valle de Aburrá** precargado (niveles de zoom 11 a 14) con conmutación automática ante caídas de internet.
* **Preservación Patrimonial y Marcas de Agua:**
  * **Original Maestro Intacto:** Las fotografías originales subidas nunca se alteran destructivamente.
  * **Derivados Web Automáticos:** Generación de copias ligeras para la web con placa institucional glassmorphism (`ARCHIVO DOCUMENTAL CEHAP • UNAL`).
  * **Descarga Segura:** Usuarios anónimos descargan la versión con marca de agua; usuarios autenticados pueden descargar el archivo maestro de alta calidad.
* **Concurrencia Multiusuario en Red Local:** Configuración optimizada de SQLite en **modo WAL (Write-Ahead Logging)** con timeout extendido, permitiendo que varios catalogadores trabajen simultáneamente desde diferentes computadores de la oficina.
* **Validación Preventiva de Archivos:** Límite configurable de 25 MB por archivo e inspección de integridad de formatos fotográficos válidos (`.jpg`, `.png`, `.webp`, `.tif`, `.bmp`).
* **Portabilidad y Respaldo Total en 1 Clic:** Herramienta de respaldo atómico (`sqlite3.backup()`) con verificación de integridad (`PRAGMA integrity_check`) para llevar el sistema completo a defensas académicas o exposiciones en memorias USB.

---

## Estructura del Repositorio

```text
├── apps/
│   ├── core/                  # Modelo abstracto base y context processors
│   ├── fotografias/           # Fichas técnicas, búsqueda inteligente, marcas de agua y mapas
│   ├── colecciones/           # Categorías, subcategorías y álbumes
│   ├── catalogacion/          # Modelos de catalogación y entidades
│   └── usuarios/              # Control de autenticación y sesiones
├── config/
│   ├── settings/
│   │   ├── base.py            # Configuración general
│   │   ├── local_windows.py   # Entorno local Windows (SQLite WAL)
│   │   └── production.py      # Entorno de producción (PostgreSQL)
│   ├── urls.py                # Enrutador principal
│   └── wsgi.py
├── static/
│   └── vendor/
│       ├── leaflet/           # Leaflet JS y CSS local
│       ├── markercluster/     # Leaflet MarkerCluster local
│       └── tiles_medellin/    # Mosaicos offline de Medellín (Z11-Z14)
├── templates/                 # Plantillas HTML responsivas
├── actualizar_universidad.bat # Script de actualización segura sin permisos de TI
├── iniciar_windows.bat        # Script de arranque en 1 clic
├── exportar_respaldo_completo.bat # Script de respaldo atómico para USB
├── exportar_respaldo.py       # Rutina de respaldo y verificación de integridad
├── generar_parche.py          # Empaquetador de parches de despliegue
├── manage.py
└── requirements.txt
```

---

## Instalación y Puesta en Marcha (Windows)

### Requisitos Previos
* **Python 3.10 o superior** instalado desde [python.org](https://www.python.org/downloads/) (asegúrate de marcar la casilla *"Add Python to PATH"* durante la instalación).

---

### Opción A: Inicio Rápido en 1 Clic (Recomendado)

1. Clona o descarga este repositorio:
   ```cmd
   git clone https://github.com/DPosso99/Archivo-CEHAP.git
   cd Archivo-CEHAP
   ```
2. Haz doble clic en el archivo:
   ```cmd
   iniciar_windows.bat
   ```
3. El script se encargará automáticamente de:
   * Crear el entorno virtual (`venv/`) e instalar las librerías necesarias.
   * Crear el archivo `.env` a partir de `.env.example`.
   * Ejecutar las migraciones de la base de datos SQLite en modo WAL.
   * Crear el usuario administrador predeterminado (`admin` / `admin`).
   * Recolectar los archivos estáticos y mosaicos locales.
   * Iniciar el servidor y abrir el navegador en `http://localhost:8000/`.

---

### Opción B: Instalación Manual por Consola

1. **Crear y activar el entorno virtual:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno:**
   Copia `.env.example` a `.env`:
   ```powershell
   copy .env.example .env
   ```

4. **Aplicar migraciones de base de datos:**
   ```powershell
   python manage.py migrate --settings=config.settings.local_windows
   ```

5. **Recolectar archivos estáticos y mosaicos:**
   ```powershell
   python manage.py collectstatic --noinput --settings=config.settings.local_windows
   ```

6. **Crear superusuario (opcional):**
   ```powershell
   python manage.py createsuperuser --settings=config.settings.local_windows
   ```

7. **Iniciar el servidor de desarrollo:**
   ```powershell
   python manage.py runserver 0.0.0.0:8000 --settings=config.settings.local_windows
   ```

Accede a la plataforma en tu navegador: [http://localhost:8000/](http://localhost:8000/).

---

## Variables de Entorno (`.env`)

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

| Variable | Descripción | Valor por defecto / Ejemplo |
| :--- | :--- | :--- |
| `SECRET_KEY` | Clave criptográfica de Django | `django-insecure-...` |
| `DEBUG` | Modo depuración | `True` en local, `False` en producción |
| `ALLOWED_HOSTS` | Hosts permitidos para conexión | `localhost,127.0.0.1,*` |
| `CARTO_API_KEY` | Clave opcional de CartoDB Voyager | *(Opcional, elimina marcas de agua externas)* |
| `GOOGLE_MAPS_API_KEY` | Clave de Google Maps Embed | *(Opcional)* |

---

## Operaciones y Scripts de Utilidad

### 1. Actualización Segura en Equipos Universitarios
```cmd
actualizar_universidad.bat
```
* **Sin permisos de Administrador ni TI.**
* Crea un respaldo previo con fecha y hora en `backups/db_respaldo_<TIMESTAMP>.sqlite3`.
* Aplica migraciones aditivas protegiendo `media/` y la base de datos existente.
* Actualiza librerías locales y genera marcas de agua para fotografías pendientes.

### 2. Exportación de Respaldo Total para Presentaciones
```cmd
exportar_respaldo_completo.bat
```
* Realiza una copia atómica con `sqlite3.backup()` sin riesgo de bloqueos.
* Valida la integridad física con `PRAGMA integrity_check;`.
* Copia todas las fotografías y código listo para correr en cualquier computador o memoria USB.

### 3. Generación por Lote de Marcas de Agua
```powershell
python manage.py generar_marcas_agua --settings=config.settings.local_windows
```
* Genera los derivados con marca de agua institucional para todas las fotografías existentes sin modificar los archivos originales. Añade `--forzar` para regenerar todos los derivados.

### 4. Pruebas Automatizadas
```powershell
python manage.py test --settings=config.settings.local_windows
```
* Ejecuta el suite completo de 16 pruebas unitarias e integración (búsquedas, mapas, calificaciones, concurrencia WAL, validaciones de archivo y preservación patrimonial).

---

## Créditos e Institución

* **Escuela del Hábitat — CEHAP**
* **Facultad de Arquitectura**
* **Universidad Nacional de Colombia — Sede Medellín**
* Plataforma desarrollada para la catalogación y divulgación del patrimonio arquitectónico y territorial.
