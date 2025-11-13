import streamlit as st
import os
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Estudiantes - Formación Intensificación", layout="wide", page_icon="⚡")
st.title("⚡ Estudiantes - Formación Intensificación")

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

# Query para estudiantes Intensificación
query = """
SELECT 
    p.ID_PERSONA,
    p.NOMBRE,
    p.APELLIDO,
    td.TIPO_DOCUMENTO,
    p.NUMERO_DOCUMENTO,
    p.EMAIL,
    p.CELULAR,
    c.NOMBRE_CIUDAD,
    i.NOMBRE_INSTITUCION,
    pnm.ESTADO
FROM Personas p
LEFT JOIN Tipo_documentos td ON p.ID_TIPO_DOCUMENTO = td.ID_TIPO_DOCUMENTO
LEFT JOIN Ciudades c ON p.ID_CIUDAD = c.ID_CIUDAD
LEFT JOIN Instituciones i ON p.ID_INSTITUCION = i.ID_INSTITUCION
LEFT JOIN Persona_Nivel_MCER pnm ON p.ID_PERSONA = pnm.ID_PERSONA
WHERE pnm.ID_CURSO = 3
ORDER BY p.APELLIDO, p.NOMBRE
"""

try:
    df = pd.read_sql(query, engine)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Estudiantes", len(df))
    with col2:
        st.metric("Ciudades", df['NOMBRE_CIUDAD'].nunique())
    with col3:
        st.metric("Instituciones", df['NOMBRE_INSTITUCION'].nunique())
    
    st.divider()
    st.subheader("Listado de Estudiantes")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
