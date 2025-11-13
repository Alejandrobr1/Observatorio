"""
Dashboard: Estudiantes por Sexo y Grado - Formación Intensificación
"""
import streamlit as st
import os
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# Intenta cargar variables de entorno (funciona en desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Si no está instalado, continúa (Streamlit Cloud usa secrets)
    pass

st.set_page_config(page_title="Sexo y Grado - Intensificación", layout="wide", page_icon="📊")

st.title("📊 Distribución por Sexo y Grado - Formación Intensificación")

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

try:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    st.sidebar.page_link("app.py", label="🏠 Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

st.sidebar.header("🔍 Filtros")

with engine.connect() as connection:
    # Obtener años disponibles
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
        st.warning("⚠️ No se encontraron datos para Formación Intensificación")
        st.stop()

    selected_year = st.sidebar.selectbox('📅 Año', available_years, index=0)

    # Query principal - SIMPLE Y COMPATIBLE
    query = text("""
        SELECT 
            COALESCE(p.SEXO, 'SIN ESPECIFICAR') as sexo,
            COALESCE(pnm.NOMBRE_CURSO, 'SIN ESPECIFICAR') as grado,
            COUNT(DISTINCT p.ID) as cantidad
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :year
        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%')
        GROUP BY COALESCE(p.SEXO, 'SIN ESPECIFICAR'), COALESCE(pnm.NOMBRE_CURSO, 'SIN ESPECIFICAR')
        ORDER BY sexo, grado
    """)
    
    result = connection.execute(query, {"year": int(selected_year)})
    data = result.fetchall()

if not data:
    st.warning(f"⚠️ No hay datos para el año {selected_year}")
    st.stop()

df = pd.DataFrame(data, columns=['Sexo', 'Grado', 'Cantidad'])

# Limpiar datos
df['Sexo_Label'] = df['Sexo'].apply(lambda x: 'Femenino' if x.lower() == 'f' else ('Masculino' if x.lower() == 'm' else 'No especificado'))
df['Grado'] = df['Grado'].fillna('Sin especificar')

# Métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("👥 Total Estudiantes", df['Cantidad'].sum())
with col2:
    st.metric("👩 Mujeres", df[df['Sexo'].str.lower() == 'f']['Cantidad'].sum())
with col3:
    st.metric("👨 Hombres", df[df['Sexo'].str.lower() == 'm']['Cantidad'].sum())

st.divider()

# Visualizaciones
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Distribución por Sexo")
    sex_data = df.groupby('Sexo_Label')['Cantidad'].sum()
    fig_sex = px.pie(
        values=sex_data.values,
        names=sex_data.index,
        title=f"Estudiantes por Sexo - {selected_year}",
        color_discrete_sequence=['#FF69B4', '#4169E1']
    )
    st.plotly_chart(fig_sex, use_container_width=True)

with col2:
    st.subheader("📈 Distribución por Grado")
    grade_data = df.groupby('Grado')['Cantidad'].sum().sort_values(ascending=False)
    fig_grade = px.bar(
        x=grade_data.index,
        y=grade_data.values,
        title=f"Estudiantes por Grado - {selected_year}",
        labels={'x': 'Grado', 'y': 'Cantidad'},
        color=grade_data.values,
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig_grade, use_container_width=True)

st.subheader("📋 Datos Detallados")
st.dataframe(df[['Sexo_Label', 'Grado', 'Cantidad']], use_container_width=True)

st.info("💡 Este dashboard muestra la distribución de estudiantes por sexo y grado en Formación Intensificación")
