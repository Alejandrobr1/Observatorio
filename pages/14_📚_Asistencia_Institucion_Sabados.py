"""
Dashboard: Asistencia por Institución - Formación Sábados
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

st.set_page_config(page_title="Asistencia Institución - Sábados", layout="wide", page_icon="🏫")

st.title("🏫 Asistencia por Institución - Formación Sábados")

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
        SELECT DISTINCT a.ANIO_REGISTRO as año
        FROM Asistencias a
        INNER JOIN Personas p ON a.PERSONA_ID = p.ID
        INNER JOIN Instituciones i ON a.INSTITUCION_ID = i.ID
        WHERE a.ANIO_REGISTRO IS NOT NULL
        AND LOWER(a.NOMBRE_CURSO) LIKE '%sabado%'
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
            COUNT(DISTINCT a.ID) as total_registros,
            SUM(CASE WHEN a.ASISTENCIA = 'Asistió' OR a.ASISTENCIA = 'S' THEN 1 ELSE 0 END) as asistencias,
            SUM(CASE WHEN a.ASISTENCIA = 'No asistió' OR a.ASISTENCIA = 'N' THEN 1 ELSE 0 END) as inasistencias,
            ROUND(SUM(CASE WHEN a.ASISTENCIA = 'Asistió' OR a.ASISTENCIA = 'S' THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT a.ID), 2) as porcentaje_asistencia
        FROM Asistencias a
        INNER JOIN Personas p ON a.PERSONA_ID = p.ID
        INNER JOIN Instituciones i ON a.INSTITUCION_ID = i.ID
        WHERE a.ANIO_REGISTRO = :year
        AND LOWER(a.NOMBRE_CURSO) LIKE '%sabado%'
        GROUP BY COALESCE(i.NOMBRE_INSTITUCION, 'SIN ESPECIFICAR')
        ORDER BY porcentaje_asistencia DESC
    """)
    
    result = connection.execute(query, {"year": int(selected_year)})
    data = result.fetchall()

if data:
    df = pd.DataFrame(data, columns=['Institución', 'Total Registros', 'Asistencias', 'Inasistencias', 'Porcentaje Asistencia'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Registros", int(df['Total Registros'].sum()))
    with col2:
        st.metric("✅ Total Asistencias", int(df['Asistencias'].sum()))
    with col3:
        st.metric("❌ Total Inasistencias", int(df['Inasistencias'].sum()))
    with col4:
        promedio = (df['Asistencias'].sum() / df['Total Registros'].sum() * 100) if df['Total Registros'].sum() > 0 else 0
        st.metric("📈 Promedio Asistencia", f"{promedio:.1f}%")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_bar = px.bar(
            df.sort_values('Porcentaje Asistencia', ascending=False),
            x='Institución',
            y='Porcentaje Asistencia',
            title=f"Porcentaje de Asistencia por Institución - {selected_year}",
            color='Porcentaje Asistencia',
            color_continuous_scale='RdYlGn',
            labels={'Porcentaje Asistencia': 'Porcentaje (%)', 'Institución': 'Institución'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        df_sorted = df.sort_values('Total Registros', ascending=True)
        fig_barh = px.barh(
            df_sorted,
            y='Institución',
            x='Total Registros',
            title=f"Total de Registros por Institución - {selected_year}",
            color='Total Registros',
            color_continuous_scale='viridis',
            labels={'Total Registros': 'Registros', 'Institución': 'Institución'}
        )
        st.plotly_chart(fig_barh, use_container_width=True)
    
    st.subheader("📋 Datos Detallados")
    st.dataframe(df, use_container_width=True)
else:
    st.warning(f"⚠️ No hay datos de asistencia para Sábados en el año {selected_year}")
