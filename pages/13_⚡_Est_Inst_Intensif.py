import streamlit as st
import os
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Estudiantes por Institución - Formación Intensificación", layout="wide", page_icon="⚡")
st.title("⚡ Estudiantes por Institución - Formación Intensificación")

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
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

try:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    st.sidebar.success("✅ Conexión establecida")
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

import pandas as pd
import plotly.express as px

# Query para Estudiantes por Institución - Intensificación
query = """
SELECT 
    p.ID_PERSONA,
    p.NOMBRE,
    p.APELLIDO,
    i.NOMBRE_INSTITUCION,
    nm.NIVEL_MCER,
    pnm.ESTADO
FROM Personas p
INNER JOIN Instituciones i ON p.ID_INSTITUCION = i.ID_INSTITUCION
INNER JOIN Persona_Nivel_MCER pnm ON p.ID_PERSONA = pnm.ID_PERSONA
INNER JOIN Nivel_MCER nm ON pnm.ID_NIVEL_MCER = nm.ID_NIVEL_MCER
WHERE pnm.ID_CURSO = 3
ORDER BY i.NOMBRE_INSTITUCION, p.APELLIDO, p.NOMBRE
"""

try:
    df = pd.read_sql(query, engine)
    
    st.subheader("Listado de Estudiantes por Institución")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Estudiantes", len(df))
    with col2:
        st.metric("Instituciones", df['NOMBRE_INSTITUCION'].nunique())
    
    st.divider()
    st.subheader("Tabla de Datos")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
