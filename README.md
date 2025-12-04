# Observatorio de Bilingüismo - Río Negro

Sistema de análisis de datos para el monitoreo del programa bilingüe de la Secretaría de Educación de Río Negro.

## Descripción General

Este proyecto es una aplicación web basada en Streamlit que proporciona análisis detallados sobre el desempeño de estudiantes y docentes en programas bilingües. Incluye datos de múltiples instituciones y períodos, con visualizaciones interactivas y métricas de rendimiento.

## Requisitos del Sistema

- Python 3.8 o superior
- MySQL 8.0 o superior
- pip (gestor de paquetes de Python)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd Observatorio
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv env
.\env\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv env
source env/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copiar `.env.example` a `.env` y configurar:

```bash
cp .env.example .env
```

Editar `.env` con credenciales de base de datos:

```
DB_USER=usuario_mysql
DB_PASS=contraseña
DB_HOST=localhost
DB_PORT=3306
DB_NAME=observatorio_bd
```

### 5. Inicializar base de datos

```bash
# Crear tablas
python data/imports/crear_tablas.py

# Importar datos
python data/imports/ejecutar_todas_las_importaciones.py
```

## Uso

### Ejecutar aplicación

```bash
streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8501`

### Estructura de navegación

La aplicación contiene 23 dashboards organizados en 4 categorías:

1. **Programa Comfenalco** (1p-9p)
   - Análisis por jornada, población, sede y nivel

2. **Período 2021-2025** (10p-15p)
   - Datos extendidos con análisis por grado e institución

3. **Programa de Intensificación** (16p-19p)
   - Seguimiento del programa bilingüe intensivo

4. **Francés Intensificación** (20p-23p)
   - Análisis específico del programa de francés

## Estructura del Proyecto

```
Observatorio/
├── app.py                    Punto de entrada de la aplicación
├── dashboard_config.py       Configuraciones y componentes compartidos
├── requirements.txt          Dependencias del proyecto
│
├── src/                      Código fuente
│   ├── config/
│   │   └── logger_config.py  Sistema de logging
│   ├── database/
│   │   ├── conexion.py       Conexión con MySQL
│   │   ├── models.py         Modelos SQLAlchemy
│   │   └── crear_tablas.py   Scripts de inicialización
│   └── utils/                Funciones auxiliares
│
├── data/                     Gestión de datos
│   ├── csv/                  Archivos fuente en CSV
│   ├── imports/              Scripts de importación
│   ├── exports/              Datos exportados
│   └── verify/               Validación de datos
│
├── pages/                    Dashboards Streamlit (23 archivos)
├── assets/                   Recursos (logos, imágenes)
├── logs/                     Registros de aplicación
│
└── .env.example             Template de configuración
```

## Estructura de Base de Datos

### Tablas principales

- **Docentes**: Información de docentes y su asignación
- **Estudiantes_2016_2019**: Datos históricos del período 2016-2019
- **Estudiantes_2021_2025**: Datos recientes del período 2021-2025
- **Estudiantes_Colombo**: Estudiantes del centro Colombo Americano
- **Escuela_nueva**: Estudiantes del programa Escuela Nueva
- **Estudiantes_intensificacion**: Datos del programa de intensificación
- **Estudiantes_frances**: Datos del programa de francés
- **Grados_2021_2025**: Información de grados por año
- **Instituciones_2021_2025**: Información de instituciones

## Características Principales

- Análisis interactivo de datos de estudiantes y docentes
- Filtros dinámicos por población, institución, jornada y período
- Visualizaciones con gráficos y tablas
- Exportación de datos
- Cálculo de métricas y estadísticas
- Soporte para múltiples programas bilingües

## Desarrollo

### Agregar un nuevo dashboard

1. Crear archivo en `pages/` con nombre: `NNp-descripcion.py`
2. Importar configuración base:

```python
import streamlit as st
from dashboard_config import create_nav_buttons
from src.database.conexion import get_engine
```

3. Implementar funciones de carga de datos y visualización

### Importar nuevos datos

1. Colocar archivo CSV en `data/csv/`
2. Crear script de importación en `data/imports/`
3. Ejecutar script:

```bash
python data/imports/insertar_datos_nuevo.py
```

## Mantenimiento

### Limpiar caché

```bash
# Limpiar caché de Streamlit
streamlit cache clear
```

### Revisar logs

```bash
# Ver logs recientes
tail -f logs/observatorio.log
```

### Respaldar datos

```bash
# Exportar datos de base de datos
mysqldump -u usuario -p nombre_bd > backup.sql
```

## Troubleshooting

### Error: No se puede conectar a la base de datos

- Verificar credenciales en `.env`
- Confirmar que MySQL está ejecutándose
- Validar que la base de datos existe

### Error: Módulo no encontrado

- Verificar que entorno virtual está activado
- Ejecutar: `pip install -r requirements.txt`

### Datos no cargan

- Ejecutar scripts de importación
- Verificar archivos CSV en `data/csv/`
- Revisar logs en `logs/`

## Contribución

Para contribuir al proyecto:

1. Crear rama: `git checkout -b feature/nueva-funcionalidad`
2. Hacer cambios y commits: `git commit -m "Descripción del cambio"`
3. Push a la rama: `git push origin feature/nueva-funcionalidad`
4. Crear Pull Request

## Licencia

Este proyecto es propiedad de la Secretaría de Educación de Río Negro.

## Contacto

Para soporte y consultas, contactar al equipo de desarrollo.

## Changelog

### Versión Actual (Producción)

- Eliminación de comentarios innecesarios y emojis
- Actualización de dependencias
- Optimización de queries
- Mejora en documentación

### Historial de versiones

Ver `CHANGELOG.md` para historial completo de cambios.

## Notas Importantes

- No modificar archivos en `env/` - es el entorno virtual
- Los logs se generan automáticamente en `logs/`
- Las exportaciones se guardan en `data/exports/`
- Respetar la estructura de directorios para mantenimiento
