# 📊 Observatorio de Bilingüismo - Estructura del Proyecto

## Estructura Organizacional

Observatorio/
├── app.py                          # Punto de entrada principal (Streamlit)
├── dashboard_config.py             # Configuración compartida de dashboards
├── requirements.txt                # Dependencias del proyecto
├── .env, .env.example              # Configuración de variables de entorno
│
├── src/                            # 📁 CÓDIGO FUENTE
│   ├── __init__.py
│   ├── config/                     # Configuraciones
│   │   ├── __init__.py
│   │   └── logger_config.py        # Sistema de logging
│   │
│   ├── database/                   # 🗄️ Módulo de Base de Datos
│   │   ├── __init__.py
│   │   ├── conexion.py             # Conexión con MySQL
│   │   ├── models.py               # Modelos SQLAlchemy
│   │   ├── crear_tablas.py         # Script de creación de tablas
│   │   └── crear_tabla_especifica.py
│   │
│   └── utils/                      # Funciones compartidas
│       └── __init__.py
│
├── data/                           # 📊 GESTIÓN DE DATOS
│   ├── csv/                        # Archivos CSV fuente
│   │   ├── Tabla_2016_2019.csv
│   │   ├── Tabla_2021_2025.csv
│   │   └── data_2025.csv
│   │
│   ├── imports/                    # 📥 Scripts de importación de datos
│   │   ├── insertar_datos_2016_2019.py
│   │   ├── insertar_datos_2021_2025.py
│   │   ├── insertar_docentes.py
│   │   ├── insertar_escuela_nueva.py
│   │   ├── insertar_estudiantes_colombo.py
│   │   └── verificar_datos_tablas.py
│   │
│   ├── exports/                    # 📤 Exportaciones de datos
│   │   └── (generado en runtime)
│   │
│   └── verify/                     # ✓ Verificación de datos
│       └── (scripts de validación)
│
├── pages/                          # 📄 PÁGINAS STREAMLIT (Activas)
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
├── dashboards_archive/             # 🗂️ DASHBOARDS ANTIGUOS (Backup)
│   ├── 1-estudiantes_por_jornada_dia.py
│   ├── 2-estudiantes_por_poblacion.py
│   └── ... (versiones antiguas)
│
├── assets/                         # 🎨 RECURSOS
│   └── Logo_rionegro.png
│
├── logs/                           # 📋 REGISTROS
│   └── (log files generados)
│
├── .streamlit/                     # ⚙️ Configuración Streamlit
├── .devcontainer/                  # 🐳 Configuración Docker Dev
├── env/                            # 🐍 Entorno Virtual (excluir de git)
└── .git/                          # 📝 Control de versiones
