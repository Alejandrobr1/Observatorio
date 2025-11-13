import streamlit as st
import os
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Niveles MCER - Formación Intensificación", layout="wide", page_icon="📚")
st.title("📚 Niveles MCER - Formación Intensificación")

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

# Query para Niveles MCER - Intensificación
query = """
SELECT 
    nm.NIVEL_MCER,
    COUNT(DISTINCT pnm.ID_PERSONA) as TOTAL
FROM Persona_Nivel_MCER pnm
INNER JOIN Nivel_MCER nm ON pnm.ID_NIVEL_MCER = nm.ID_NIVEL_MCER
WHERE pnm.ID_CURSO = 3
GROUP BY nm.NIVEL_MCER
ORDER BY TOTAL DESC
"""

try:
    df = pd.read_sql(query, engine)
    
    st.subheader("Distribución de Estudiantes por Nivel MCER")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(df, names='NIVEL_MCER', values='TOTAL', title="Proporción de Niveles")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig_bar = px.bar(df, x='NIVEL_MCER', y='TOTAL', title="Cantidad por Nivel")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()
    st.subheader("Tabla de Datos")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
