import os

# Configuración de los 14 dashboards
dashboards = [
    {
        "num": 1,
        "emoji": "📊",
        "title": "Estudiantes - Formación Sábados",
        "icon": "📊",
        "type": "listado"
    },
    {
        "num": 2,
        "emoji": "👥",
        "title": "Sexo y Grado - Formación Sábados",
        "icon": "👥",
        "type": "analisis"
    },
    {
        "num": 3,
        "emoji": "👥",
        "title": "Sexo y Grado - Formación Docentes",
        "icon": "👥",
        "type": "analisis"
    },
    {
        "num": 4,
        "emoji": "⚡",
        "title": "Estudiantes - Formación Intensificación",
        "icon": "⚡",
        "type": "listado"
    },
    {
        "num": 5,
        "emoji": "📈",
        "title": "Sexo y Grado - Formación Intensificación",
        "icon": "📈",
        "type": "analisis"
    },
    {
        "num": 6,
        "emoji": "📊",
        "title": "Estado - Formación Sábados",
        "icon": "📊",
        "type": "estado"
    },
    {
        "num": 7,
        "emoji": "⚡",
        "title": "Estado - Formación Intensificación",
        "icon": "⚡",
        "type": "estado"
    },
    {
        "num": 8,
        "emoji": "📚",
        "title": "Niveles MCER - Formación Sábados",
        "icon": "📚",
        "type": "niveles"
    },
    {
        "num": 9,
        "emoji": "📚",
        "title": "Niveles MCER - Formación Intensificación",
        "icon": "📚",
        "type": "niveles"
    },
    {
        "num": 10,
        "emoji": "🏫",
        "title": "Instituciones - Formación Sábados",
        "icon": "🏫",
        "type": "instituciones"
    },
    {
        "num": 11,
        "emoji": "🏫",
        "title": "Instituciones - Formación Intensificación",
        "icon": "🏫",
        "type": "instituciones"
    },
    {
        "num": 12,
        "emoji": "🏫",
        "title": "Estudiantes por Institución - Formación Docentes",
        "icon": "🏫",
        "type": "institucion_analisis"
    },
    {
        "num": 13,
        "emoji": "⚡",
        "title": "Estudiantes por Institución - Formación Intensificación",
        "icon": "⚡",
        "type": "institucion_analisis"
    },
    {
        "num": 14,
        "emoji": "📚",
        "title": "Estudiantes por Institución - Formación Sábados",
        "icon": "📚",
        "type": "institucion_analisis"
    }
]

template = """import streamlit as st
import os
from sqlalchemy import create_engine, text

st.set_page_config(page_title="{title}", layout="wide", page_icon="{emoji}")
st.title("{emoji} {title}")

@st.cache_resource
def get_engine():
    try:
        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))
        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))
        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))
        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))
        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))
    except FileNotFoundError:
        db_user = os.getenv('DB_USER', 'root')
        db_pass = os.getenv('DB_PASS', '123456')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '3308')
        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    connection_string = f"mysql+mysqlconnector://{{db_user}}:{{db_pass}}@{{db_host}}:{{db_port}}/{{db_name}}"
    return create_engine(connection_string)

try:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    st.sidebar.success("✅ Conexión establecida")
except Exception as e:
    st.error(f"❌ Error de conexión: {{e}}")
    st.stop()

st.info("Dashboard: {title}")
"""

# Crear los archivos
base_path = "pages"
for dashboard in dashboards:
    filename = f"{base_path}/{dashboard['num']}_{dashboard['emoji']}_{"_".join(dashboard['title'].split(" - ")[0].split())}.py"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(template.format(
            title=dashboard['title'],
            emoji=dashboard['emoji']
        ))
    print(f"✅ Creado: {filename}")

print(f"\n✅ Se crearon {len(dashboards)} dashboards correctamente")
