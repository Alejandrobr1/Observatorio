"""
Dashboard: Instituciones - Formación Intensificación
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

st.set_page_config(page_title="Instituciones - Intensificación", layout="wide", page_icon="🏫")

st.title("🏫 Distribución por Institución - Formación Intensificación")

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
    st.sidebar.page_link("app.py", label="🏠 Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()

st.sidebar.header("🔍 Filtros")

with engine.connect() as connection:
    query_years = text("""
        SELECT DISTINCT pnm.ANIO_REGISTRO as año
        FROM Persona_Nivel_MCER pnm
        WHERE pnm.ANIO_REGISTRO IS NOT NULL
        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%')
        ORDER BY año DESC
    """)
    result_years = connection.execute(query_years)
    available_years = [str(int(row[0])) for row in result_years.fetchall() if row[0]]

    if not available_years:
        st.warning("⚠️ No hay datos disponibles")
        st.stop()

    selected_year = st.sidebar.selectbox('📅 Año', available_years, index=0)

with engine.connect() as connection:
    query = text("""
        SELECT 
            COALESCE(i.NOMBRE_INSTITUCION, 'SIN ESPECIFICAR') as institucion,
            COUNT(DISTINCT p.ID) as cantidad
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        LEFT JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
        WHERE pnm.ANIO_REGISTRO = :year
        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%')
        GROUP BY COALESCE(i.NOMBRE_INSTITUCION, 'SIN ESPECIFICAR')
        ORDER BY cantidad DESC
    """)
    
    result = connection.execute(query, {"year": int(selected_year)})
    data = result.fetchall()

if data:
    df = pd.DataFrame(data, columns=['Institución', 'Cantidad'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👥 Total Estudiantes", df['Cantidad'].sum())
    with col2:
        st.metric("🏫 Instituciones", len(df))
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(
            df,
            values='Cantidad',
            names='Institución',
            title=f"Distribución por Institución - {selected_year}"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        df_sorted = df.sort_values('Cantidad', ascending=True)
        fig_bar = px.bar(
            df_sorted,
            y='Institución',
            x='Cantidad',
            title=f"Estudiantes por Institución - {selected_year}",
            color='Cantidad',
            color_continuous_scale='viridis',
            labels={'Cantidad': 'Cantidad', 'Institución': 'Institución'},
            orientation='h'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.subheader("📋 Datos Detallados")
    st.dataframe(df, use_container_width=True)
else:
    st.warning(f"⚠️ No hay datos para el año {selected_year}")
