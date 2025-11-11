import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import os

st.set_page_config(page_title="Estudiantes Sábados", layout="wide", page_icon="📊")

st.title("📊 Estudiantes - Formación Sábados")

@st.cache_resource
def get_engine():
    # Primero intenta obtener de st.secrets (Streamlit Cloud)
    # Si no está disponible, usa variables de entorno
    try:
        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))
        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))
        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))
        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))
        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))
    except FileNotFoundError:
        # Si secrets.toml no existe, usa solo variables de entorno
        db_user = os.getenv('DB_USER', 'root')
        db_pass = os.getenv('DB_PASS', '123456')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '3308')
        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

@st.cache_data
def get_estudiantes_sabados():
    engine = get_engine()
    query = """
    SELECT 
        p.NOMBRES,
        p.APELLIDOS,
        p.SEXO,
        nm.NIVEL_MCER,
        p.GRADO,
        pnm.ANIO_REGISTRO,
        pnm.NOMBRE_CURSO,
        i.NOMBRE_INSTITUCION,
        ci.NOMBRE_CIUDAD,
        p.TIPO_POBLACION
    FROM Persona_Nivel_MCER pnm
    JOIN Personas p ON pnm.PERSONA_ID = p.ID
    JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID
    JOIN Instituciones i ON nm.INSTITUCION_ID = i.ID
    JOIN Ciudades ci ON i.CIUDAD_ID = ci.ID
    WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%sabados%'
    ORDER BY pnm.ANIO_REGISTRO DESC, p.NOMBRES
    """
    return pd.read_sql(text(query), engine)

try:
    df = get_estudiantes_sabados()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Estudiantes", len(df))
    col2.metric("📅 Años", df['ANIO_REGISTRO'].nunique())
    col3.metric("🎓 Niveles", df['NIVEL_MCER'].nunique())
    col4.metric("🏫 Instituciones", df['NOMBRE_INSTITUCION'].nunique())
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Distribución", "Por Año", "Por Institución", "Datos"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(
                df.groupby('NIVEL_MCER').size().reset_index(name='count'),
                names='NIVEL_MCER',
                values='count',
                title='Distribución por Nivel MCER'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                df.groupby('SEXO').size().reset_index(name='count'),
                names='SEXO',
                values='count',
                title='Distribución por Sexo'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.bar(
            df.groupby('ANIO_REGISTRO').size().reset_index(name='count'),
            x='ANIO_REGISTRO',
            y='count',
            title='Estudiantes por Año',
            labels={'count': 'Cantidad', 'ANIO_REGISTRO': 'Año'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        inst_data = df.groupby('NOMBRE_INSTITUCION').size().reset_index(name='count').sort_values('count', ascending=False)
        fig = px.bar(
            inst_data,
            y='NOMBRE_INSTITUCION',
            x='count',
            title='Estudiantes por Institución',
            labels={'count': 'Cantidad', 'NOMBRE_INSTITUCION': 'Institución'},
            orientation='h'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
