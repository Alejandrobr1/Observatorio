# 📊 PROYECTO: Observatorio de Bilingüismo
# Estructura Organizacional Final

```
Observatorio/
│
├── 🔵 ARCHIVOS PRINCIPALES
│   ├── app.py                      (Punto de entrada Streamlit)
│   ├── dashboard_config.py         (Config compartida - Navbar, Filtros)
│   ├── requirements.txt            (Dependencias)
│   ├── .env.example               (Template de variables de entorno)
│   └── migrate_imports.py         (Script de migración - ya ejecutado)
│
├── 📁 src/                         (CÓDIGO FUENTE ORGANIZADO)
│   ├── __init__.py
│   │
│   ├── config/                     (Configuraciones)
│   │   ├── __init__.py
│   │   └── logger_config.py        (Sistema de logging centralizado)
│   │
│   ├── database/                   (🗄️ Módulo de Base de Datos)
│   │   ├── __init__.py
│   │   ├── conexion.py             (Conexión MySQL + Engine)
│   │   ├── models.py               (Modelos SQLAlchemy)
│   │   ├── crear_tablas.py         (Crear schema de BD)
│   │   └── crear_tabla_especifica.py
│   │
│   └── utils/                      (Utilidades compartidas)
│       └── __init__.py
│
├── 📊 data/                        (GESTIÓN DE DATOS)
│   ├── csv/                        (📥 Archivos fuente)
│   │   ├── Tabla_2016_2019.csv
│   │   ├── Tabla_2021_2025.csv
│   │   └── data_2025.csv
│   │
│   ├── imports/                    (📤 Scripts de importación)
│   │   ├── insertar_datos_2016_2019.py
│   │   ├── insertar_datos_2021_2025.py
│   │   ├── insertar_docentes.py
│   │   ├── insertar_escuela_nueva.py
│   │   ├── insertar_estudiantes_colombo.py
│   │   └── verificar_datos_tablas.py
│   │
│   ├── exports/                    (📋 Exportaciones generadas)
│   └── verify/                     (✓ Validación)
│
├── 📄 pages/                       (DASHBOARDS ACTIVOS)
│   ├── 1p-estudiantes_por_jornada_dia.py
│   ├── 2p-estudiantes_por_poblacion.py
│   ├── 3p-estudiantes_por_sede_nodal_etapa1_2.py
│   ├── 4p-estudiantes_por_sede_nodal_barras_etp1_2.py
│   ├── 5p-estudiantes_por_institucion.py
│   ├── 6p-docentes_por_nivel.py
│   ├── 7p-docentes_por_institucion.py
│   ├── 8p-colombo_por_institucion.py
│   ├── 9p-colombo_por_nivel.py
│   ├── 10p-estudiantes_por_institucion_2021_2025.py
│   ├── 11p-estudiantes_por_grado_2021_2025.py
│   └── __pycache__/
│
├── 🗂️ dashboards_archive/          (VERSIONES ANTIGUAS - BACKUP)
│   ├── 1-estudiantes_por_jornada_dia.py
│   ├── 2-estudiantes_por_poblacion.py
│   ├── ...
│   ├── 9-colombo_por_nivel.py
│   └── __pycache__/
│
├── 🎨 assets/                      (RECURSOS)
│   └── Logo_rionegro.png
│
├── 📋 logs/                        (REGISTROS)
│   └── (generados automáticamente)
│
├── ⚙️ .streamlit/                  (Config Streamlit)
│   └── config.toml
│
├── 🐳 .devcontainer/               (Dev container config)
│
├── 🐍 env/                         (Virtual environment - excluir git)
│   ├── Scripts/, Lib/, Include/
│   └── pyvenv.cfg
│
├── 📝 .git/                        (Control de versiones)
├── .gitignore                     (Reglas de exclusión)
│
└── 📖 README.md & README_ESTRUCTURA.md


═══════════════════════════════════════════════════════════════════════

🔄 CAMBIOS REALIZADOS:

✅ Base de Datos
   OLD: Base_datos/conexion.py        → NEW: src/database/conexion.py
   OLD: Base_datos/models.py          → NEW: src/database/models.py
   OLD: Base_datos/crear_tablas.py    → NEW: src/database/crear_tablas.py
   OLD: Base_datos/crear_tabla_especifica.py → NEW: src/database/crear_tabla_especifica.py

✅ Configuración
   OLD: logger_config.py              → NEW: src/config/logger_config.py

✅ Datos
   OLD: Queries/insertar_*.py         → NEW: data/imports/insertar_*.py
   OLD: CSVs/                         → NEW: data/csv/
   OLD: Base_datos/logs/ → RENAMED   → NEW: data/verify/ (verificación)

✅ Dashboards
   OLD: Dashboards/                   → NEW: dashboards_archive/ (backup)
   KEEP: pages/ (activos)             ✓ Sin cambios

═══════════════════════════════════════════════════════════════════════

🎯 FUNCIONALIDAD:
   ✓ Todos los dashboards siguen funcionando
   ✓ Importaciones actualizadas automáticamente
   ✓ Sistema modular y escalable
   ✓ Mejor organización para mantenimiento
   ✓ Base para crecimiento futuro

🚀 EJECUCIÓN:
   streamlit run app.py

═══════════════════════════════════════════════════════════════════════
```
