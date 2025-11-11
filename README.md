# 📊 Observatorio de Bilingüismo

> Sistema de monitoreo y análisis de programas educativos de bilingüismo

[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.1-FF4B4B?style=flat-square&logo=streamlit)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python)](https://python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat-square&logo=mysql)](https://mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

## 🚀 Inicio Rápido

### Opción 1: Desplegar en Streamlit Cloud (Recomendado)

```bash
# 1. Subir a GitHub
git add .
git commit -m "Preparar para Streamlit Cloud"
git push

# 2. En https://share.streamlit.io
# - Conecta tu repositorio
# - Selecciona: Dashboards/main_dashboard.py
# - Configura secrets en App settings

# 3. Tu app estará en:
# https://observatorio-bilinguismo.streamlit.app/
```

📚 Ver: [GUIA_DESPLIEGUE_RAPIDA.md](GUIA_DESPLIEGUE_RAPIDA.md)

### Opción 2: Ejecutar Localmente

```bash
# 1. Crear ambiente virtual
python -m venv env
.\env\Scripts\Activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear archivo de secretos local
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# 4. Ejecutar aplicación
streamlit run Dashboards/main_dashboard.py
```

La app abrirá en: `http://localhost:8501`

## 📋 Contenido del Proyecto

```
├── 🏠 Página Principal (Dashboards/main_dashboard.py)
│   ├── Inicio: Descripción y métricas
│   ├── Dashboards: Acceso a todas las páginas
│   └── Descargas: Exportar datos en ZIP/CSV
│
├── 📑 Dashboards Multipage (pages/)
│   ├── Estudiantes Sábados
│   ├── Sexo y Grado
│   └── (Agrega más fácilmente)
│
├── 💾 Base de Datos
│   ├── conexion.py: Conexión MySQL
│   ├── crear_tablas.py: Crear estructura
│   └── models.py: Modelos SQLAlchemy
│
├── 📊 Importación
│   ├── CSV_GENERAL.py: Importar todos los datos
│   └── CSV_GENERAL_INTENSIFICACION.py: Datos intensificación
│
└── 📚 Documentación
    ├── GUIA_DESPLIEGUE_RAPIDA.md
    ├── DESPLIEGUE_STREAMLIT_CLOUD.md
    └── EJEMPLOS_DASHBOARDS_MULTIPAGE.py
```

## ✨ Características

- 🎨 **Interfaz Moderna**: Diseño profesional con Streamlit
- 📈 **Dashboards Interactivos**: Gráficos con Plotly
- 🔄 **Navegación Automática**: Detecta páginas en `pages/`
- 💾 **Exportación de Datos**: ZIP y CSV
- 🔐 **Seguro**: Credenciales en secretos, no en código
- ☁️ **Cloud Ready**: Compatible con Streamlit Cloud
- 📊 **Multiproblema**: Sábados, Docentes, Intensificación
- 🚀 **Escalable**: Fácil agregar más dashboards

## 📊 Datos Disponibles

- **👥 Total Personas**: 7,686+ (Sábados) + 957 (Docentes) + 2,507 (Intensificación)
- **📅 Período**: 2016-2025 (10 años)
- **🏫 Instituciones**: Múltiples municipios de Río Negro
- **🎓 Niveles MCER**: A1, A2, B1, B2, C1, C2
- **📍 Ciudades**: Bariloche, Dina Huapi, San Martín de los Andes, Villa La Angostura

## 🔧 Requisitos

- Python 3.8+
- MySQL 8.0+
- Navegador moderno

Dependencias automáticas en `requirements.txt`:
- streamlit
- pandas
- sqlalchemy
- mysql-connector-python
- plotly
- Y más...

## 🌐 Opciones de Base de Datos en la Nube

Para Streamlit Cloud, necesitas BD en la nube:

| Proveedor | Costo | Facilidad | Recomendación |
|-----------|-------|----------|---------------|
| **AWS RDS** | ~$15/mes | Media | ⭐ Recomendado |
| **Clever Cloud** | ~$20/mes | Fácil | ✅ Buena opción |
| **Digital Ocean** | ~$15/mes | Fácil | ✅ Buena opción |
| **Railway** | Gratis/mes | Muy fácil | ✅ Para pruebas |

→ Más info en [DESPLIEGUE_STREAMLIT_CLOUD.md](DESPLIEGUE_STREAMLIT_CLOUD.md)

## 🎯 Agregar Dashboards

Crear nuevo dashboard es muy fácil:

```python
# pages/3_📊_Mi_Dashboard.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

st.set_page_config(page_title="Mi Dashboard")
st.title("📊 Mi Dashboard")

@st.cache_resource
def get_engine():
    return create_engine(
        f"mysql+mysqlconnector://"
        f"{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )

@st.cache_data
def get_data():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM Personas LIMIT 10", engine)

df = get_data()
st.dataframe(df)
```

Streamlit detectará automáticamente el archivo y lo agregará al menú lateral.

→ Ejemplos completos: [EJEMPLOS_DASHBOARDS_MULTIPAGE.py](EJEMPLOS_DASHBOARDS_MULTIPAGE.py)

## 🔐 Configuración de Seguridad

### Local (Desarrollo)

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edita `.streamlit/secrets.toml`:
```toml
DB_USER = "root"
DB_PASS = "123456"
DB_HOST = "localhost"
DB_PORT = "3308"
DB_NAME = "observatorio_bilinguismo"
```

### Cloud (Producción)

En Streamlit Cloud → App settings → Secrets:
```toml
DB_USER = "admin"
DB_PASS = "contraseña_segura"
DB_HOST = "tu-host.rds.amazonaws.com"
DB_PORT = "3306"
DB_NAME = "observatorio_bilinguismo"
```

**⚠️ IMPORTANTE**: Nunca subas `.env` o `secrets.toml` a GitHub. Están en `.gitignore`.

## 📚 Documentación

- 📖 [Guía Despliegue Rápida](GUIA_DESPLIEGUE_RAPIDA.md) - 5 pasos en 15 min
- 📘 [Despliegue Completo](DESPLIEGUE_STREAMLIT_CLOUD.md) - Guía técnica
- 💻 [Ejemplos Dashboards](EJEMPLOS_DASHBOARDS_MULTIPAGE.py) - Código de ejemplo
- 📋 [Resumen Cambios](RESUMEN_CAMBIOS_DESPLIEGUE.txt) - Qué se preparó

## 🚀 Scripts de Despliegue

### PowerShell (Windows)
```powershell
.\DESPLIEGUE_STREAMLIT_CLOUD.ps1
```

### Python (Multiplataforma)
```bash
python desplegar_streamlit_cloud.py
```

Ambos scripts ayudan a:
- Verificar Git
- Validar estructura
- Configurar remoto
- Hacer commits

## 🤝 Contribuir

Para agregar funcionalidades:

1. Crea rama: `git checkout -b feature/mi-feature`
2. Haz cambios y commit: `git commit -m "Agregar feature"`
3. Push: `git push origin feature/mi-feature`
4. Abre Pull Request

## 📞 Soporte

- 📚 [Documentación Streamlit](https://docs.streamlit.io/)
- 🐍 [Pandas Docs](https://pandas.pydata.org/)
- 📊 [Plotly Express](https://plotly.com/python/plotly-express/)
- 🗄️ [SQLAlchemy](https://www.sqlalchemy.org/)

## 📜 License

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## ✅ Checklist de Despliegue

- [ ] Crear repositorio en GitHub
- [ ] Subir código a GitHub
- [ ] Crear BD en la nube (AWS/Clever/Digital Ocean)
- [ ] Obtener credenciales de BD
- [ ] Crear app en Streamlit Cloud
- [ ] Configurar Secrets
- [ ] Crear tablas en BD remota
- [ ] Importar datos
- [ ] Verificar app en línea
- [ ] Compartir URL con usuarios

---

**Hecho con ❤️ para el Observatorio de Bilingüismo**

Última actualización: 2025 | Versión: 1.0
