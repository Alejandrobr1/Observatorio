# 📊 Observatorio de Bilingüismo - Estructura del Proyecto

## Estructura Organizacional

```
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
```

## 🔄 Cambios Realizados

### 1. **Módulo `src/database/`**
   - Consolidación de módulos de base de datos
   - Archivos movidos desde `Base_datos/`:
     - `conexion.py` - Conexión MySQL
     - `models.py` - Modelos de datos
     - `crear_tablas.py` - Creación de esquema
     - `crear_tabla_especifica.py` - Creación selectiva

### 2. **Módulo `src/config/`**
   - `logger_config.py` - Sistema de logging centralizado

### 3. **Directorio `data/`**
   - `data/csv/` - Almacena archivos CSV fuente
   - `data/imports/` - Scripts para importar datos
   - `data/exports/` - Exportaciones generadas
   - `data/verify/` - Validación de datos

### 4. **Dashboards**
   - `pages/` - Dashboards activos (1p-11p)
   - `dashboards_archive/` - Versiones antiguas (1-9)

## 🚀 Importaciones Actualizadas

### Antes (Estructura Antigua)
```python
from Base_datos.conexion import get_engine
from logger_config import get_logger
```

### Después (Nueva Estructura)
```python
from src.database.conexion import get_engine
from src.config.logger_config import get_logger
```

## 📌 Puntos Importantes

- ✅ Todas las funcionalidades se mantienen intactas
- ✅ Los dashboards siguen funcionando sin cambios
- ✅ Sistema modular y escalable
- ✅ Mejor organización para mantenimiento
- ✅ Facilita testing y desarrollo futuro

## 🔧 Para Ejecutar

```bash
# Activar entorno virtual
.\env\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar Streamlit
streamlit run app.py
```

## 📊 Estructura de Datos

### Tablas Principales
- `Docentes` - Información de docentes
- `Estudiantes_2016_2019` - Datos históricos
- `Estudiantes_2021_2025` - Datos recientes
- `Estudiantes_Colombo` - Centro Colombo Americano
- `Escuela_nueva` - Programa Escuela Nueva

## 📝 Notas
- Los archivos antiguos se conservan en `dashboards_archive/` como respaldo
- Los logs se generan automáticamente en `logs/`
- Las exportaciones se guardan en `data/exports/`
