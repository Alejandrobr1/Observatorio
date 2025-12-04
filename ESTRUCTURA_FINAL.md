# 📊 PROYECTO: Observatorio de Bilingüismo

# Estructura Organizacional Final

Observatorio/
│
├── 🔵 ARCHIVOS PRINCIPALES
│   ├── app.py                      (Punto de entrada Streamlit)
│   ├── dashboard_config.py         (Config compartida - Navbar, Filtros)
│   ├── requirements.txt            (Dependencias)
│   ├── .env.example               (Template de variables de entorno)  
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
│   │   ├── crear_tabla_especifica.py
│   │   └── migrate_imports.py         (Script de migración - ya ejecutado)
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

🚀 EJECUCIÓN:
   streamlit run app.py

═══════════════════════════════════════════════════════════════════════
