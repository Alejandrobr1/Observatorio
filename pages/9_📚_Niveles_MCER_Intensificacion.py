"""
Dashboard: Niveles MCER - Formación Intensificación
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

st.set_page_config(page_title="Niveles MCER - Intensificación", layout="wide", page_icon="📚")

st.title("📚 Distribución por Nivel MCER - Formación Intensificación")

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
            COALESCE(n.NIVEL_MCER, 'SIN ESPECIFICAR') as nivel,
            COALESCE(p.SEXO, 'SIN ESPECIFICAR') as sexo,
            COUNT(DISTINCT p.ID) as cantidad
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        LEFT JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
        WHERE pnm.ANIO_REGISTRO = :year
        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%')
        GROUP BY COALESCE(n.NIVEL_MCER, 'SIN ESPECIFICAR'), COALESCE(p.SEXO, 'SIN ESPECIFICAR')
        ORDER BY nivel, sexo
    """)
    
    result = connection.execute(query, {"year": int(selected_year)})
    data = result.fetchall()

if data:
    df = pd.DataFrame(data, columns=['Nivel', 'Sexo', 'Cantidad'])
    
    # Normalizar sexo
    df['Sexo_Label'] = df['Sexo'].apply(
        lambda x: 'Femenino' if x.lower() == 'f' else ('Masculino' if x.lower() == 'm' else 'Otro')
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Total", df['Cantidad'].sum())
    with col2:
        st.metric("📚 Niveles", df['Nivel'].nunique())
    with col3:
        st.metric("👥 Sexos", df['Sexo_Label'].nunique())
    
    st.divider()
    
    # Gráfico de barras agrupadas
    fig_bar = px.bar(
        df,
        x='Nivel',
        y='Cantidad',
        color='Sexo_Label',
        title=f"Estudiantes por Nivel MCER - {selected_year}",
        barmode='group',
        color_discrete_map={'Masculino': '#3498db', 'Femenino': '#e74c3c', 'Otro': '#95a5a6'},
        labels={'Cantidad': 'Cantidad', 'Nivel': 'Nivel MCER', 'Sexo_Label': 'Sexo'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.subheader("📋 Datos Detallados")
    st.dataframe(df[['Nivel', 'Sexo_Label', 'Cantidad']], use_container_width=True)
else:
    st.warning(f"⚠️ No hay datos para el año {selected_year}")
