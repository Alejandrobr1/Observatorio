import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import os

st.set_page_config(page_title="Sexo y Grado - Sábados", layout="wide", page_icon="👥")

st.title("👥 Sexo y Grado - Formación Sábados")

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

@st.cache_data
def get_data_sexo_grado():
    engine = get_engine()
    query = """
    SELECT
        pnm.NOMBRE_CURSO as grado,
        p.SEXO,
        COUNT(*) as cantidad,
        pnm.ANIO_REGISTRO
    FROM Persona_Nivel_MCER pnm
    JOIN Personas p ON pnm.PERSONA_ID = p.ID
    WHERE pnm.NOMBRE_CURSO LIKE '%Sabados%' OR pnm.NOMBRE_CURSO LIKE '%sabados%'
    GROUP BY pnm.NOMBRE_CURSO, p.SEXO, pnm.ANIO_REGISTRO
    ORDER BY pnm.NOMBRE_CURSO, p.SEXO
    """
    return pd.read_sql(text(query), engine)

try:
    df = get_data_sexo_grado()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Registros Total", len(df))
    col2.metric("👥 Sexos", df['SEXO'].nunique())
    col3.metric("🎓 Grados", df['GRADO'].nunique())
    
    st.divider()
    
    # Gráfico de sexo y grado
    sexo_grado = df.groupby(['grado', 'SEXO'])['cantidad'].sum().reset_index()
    
    fig1 = px.bar(
        sexo_grado,
        x='grado',
        y='cantidad',
        color='SEXO',
        barmode='group',
        title='Distribución por Grado y Sexo',
        labels={'cantidad': 'Cantidad', 'grado': 'Grado', 'SEXO': 'Sexo'}
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Tabla de datos
    st.subheader("📋 Datos detallados")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
