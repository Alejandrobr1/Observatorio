"""
Dashboard: Análisis de Estudiantes por Institución - Formación Sábados
"""
import streamlit as st
import os
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

st.set_page_config(page_title="Estudiantes por Institución - Sábados", layout="wide", page_icon="📚")

st.title("📚 Estudiantes por Institución - Formación Sábados")

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
    st.error(f"❌ Error: {e}")
    st.stop()

st.sidebar.header("🔍 Filtros")

with engine.connect() as connection:
    query_years = text("""
        SELECT DISTINCT pnm.ANIO_REGISTRO as año
        FROM Persona_Nivel_MCER pnm
        WHERE pnm.ANIO_REGISTRO IS NOT NULL
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%sabado%'
        ORDER BY año DESC
    """)
    result_years = connection.execute(query_years)
    available_years = [str(int(row[0])) for row in result_years.fetchall() if row[0]]

    if not available_years:
        st.warning("⚠️ No hay datos disponibles para Sábados")
        st.stop()

    selected_year = st.sidebar.selectbox('📅 Año', available_years, index=0)

with engine.connect() as connection:
    query = text("""
        SELECT 
            COALESCE(i.NOMBRE_INSTITUCION, 'SIN ESPECIFICAR') as institucion,
            COUNT(DISTINCT p.ID) as total_estudiantes,
            COUNT(DISTINCT CASE WHEN p.SEXO = 'F' THEN p.ID END) as mujeres,
            COUNT(DISTINCT CASE WHEN p.SEXO = 'M' THEN p.ID END) as hombres,
            COUNT(DISTINCT nm.NIVEL_MCER) as niveles_mcer,
            ROUND(COUNT(DISTINCT CASE WHEN p.SEXO = 'F' THEN p.ID END) * 100.0 / COUNT(DISTINCT p.ID), 2) as porcentaje_mujeres
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        LEFT JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID
        LEFT JOIN Instituciones i ON nm.INSTITUCION_ID = i.ID
        WHERE pnm.ANIO_REGISTRO = :year
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%sabado%'
        GROUP BY COALESCE(i.NOMBRE_INSTITUCION, 'SIN ESPECIFICAR')
        ORDER BY total_estudiantes DESC
    """)
    
    result = connection.execute(query, {"year": int(selected_year)})
    data = result.fetchall()

if data:
    df = pd.DataFrame(data, columns=['Institución', 'Total Estudiantes', 'Mujeres', 'Hombres', 'Niveles MCER', 'Porcentaje Mujeres'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Estudiantes", int(df['Total Estudiantes'].sum()))
    with col2:
        st.metric("👩 Total Mujeres", int(df['Mujeres'].sum()))
    with col3:
        st.metric("👨 Total Hombres", int(df['Hombres'].sum()))
    with col4:
        st.metric("🏫 Instituciones", len(df))
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_bar = px.bar(
            df.sort_values('Total Estudiantes', ascending=False),
            x='Institución',
            y='Total Estudiantes',
            title=f"Estudiantes por Institución - {selected_year}",
            color='Total Estudiantes',
            color_continuous_scale='viridis',
            labels={'Total Estudiantes': 'Estudiantes', 'Institución': 'Institución'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        df_sorted = df.sort_values('Porcentaje Mujeres', ascending=False)
        fig_sex = px.bar(
            df_sorted,
            x='Institución',
            y=['Mujeres', 'Hombres'],
            title=f"Distribución por Género - {selected_year}",
            barmode='stack',
            labels={'value': 'Cantidad', 'Institución': 'Institución'},
            color_discrete_map={'Mujeres': '#FF69B4', 'Hombres': '#4169E1'}
        )
        st.plotly_chart(fig_sex, use_container_width=True)
    
    st.subheader("📋 Datos Detallados")
    st.dataframe(df, use_container_width=True)
else:
    st.warning(f"⚠️ No hay datos para Sábados en el año {selected_year}")
