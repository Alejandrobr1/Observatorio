import streamlit as st
import os
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Sexo y Grado - Formación Intensificación", layout="wide", page_icon="📈")
st.title("📈 Sexo y Grado - Formación Intensificación")

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

# Query para Sexo y Grado - Intensificación
query = """
SELECT 
    p.SEXO,
    c.NOMBRE_CURSO as GRADO,
    COUNT(DISTINCT p.ID_PERSONA) as TOTAL
FROM Personas p
LEFT JOIN Persona_Nivel_MCER pnm ON p.ID_PERSONA = pnm.ID_PERSONA
LEFT JOIN Cursos c ON pnm.ID_CURSO = c.ID_CURSO
WHERE pnm.ID_CURSO = 3
GROUP BY p.SEXO, c.NOMBRE_CURSO
ORDER BY c.NOMBRE_CURSO, p.SEXO
"""

try:
    df = pd.read_sql(query, engine)
    
    st.subheader("Distribución por Sexo y Grado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico por Sexo
        sexo_df = df.groupby('SEXO')['TOTAL'].sum().reset_index()
        fig_sexo = px.bar(sexo_df, x='SEXO', y='TOTAL', title="Por Sexo", labels={'TOTAL': 'Cantidad', 'SEXO': 'Sexo'})
        st.plotly_chart(fig_sexo, use_container_width=True)
    
    with col2:
        # Gráfico por Grado
        grado_df = df.groupby('GRADO')['TOTAL'].sum().reset_index()
        fig_grado = px.bar(grado_df, x='GRADO', y='TOTAL', title="Por Grado", labels={'TOTAL': 'Cantidad', 'GRADO': 'Grado'})
        st.plotly_chart(fig_grado, use_container_width=True)
    
    st.divider()
    st.subheader("Tabla de Datos")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
