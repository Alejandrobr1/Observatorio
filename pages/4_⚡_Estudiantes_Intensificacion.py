"""
Dashboard: Estudiantes en Formación Intensificación
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

st.set_page_config(page_title="Estudiantes Intensificación", layout="wide", page_icon="⚡")

st.title("⚡ Estudiantes en Formación Intensificación")

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
    st.sidebar.success("✅ Conexión establecida")
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

st.sidebar.header("🔍 Filtros")

with engine.connect() as connection:
    # Obtener años disponibles
    query_years = text("""
        SELECT DISTINCT pnm.ANIO_REGISTRO as año
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO IS NOT NULL
        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%')
        AND p.TIPO_PERSONA = 'Estudiante'
        ORDER BY año DESC
    """)
    result_years = connection.execute(query_years)
    available_years = [str(int(row[0])) for row in result_years.fetchall() if row[0]]

    if not available_years:
        st.warning("⚠️ No se encontraron datos para Formación Intensificación")
        st.stop()

    selected_year = st.sidebar.selectbox('📅 Año', available_years, index=0)

    # Query principal
    query = text("""
        SELECT 
            p.NÚMERO_DE_IDENTIFICACIÓN,
            p.NOMBRES,
            p.APELLIDOS,
            p.SEXO,
            pnm.NIVEL_MCER,
            pnm.GRADO,
            pnm.ANIO_REGISTRO,
            pnm.NOMBRE_CURSO,
            i.NOMBRE_INSTITUCION,
            ci.NOMBRE_CIUDAD
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        LEFT JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID
        LEFT JOIN Instituciones i ON nm.INSTITUCION_ID = i.ID
        LEFT JOIN Ciudades ci ON i.CIUDAD_ID = ci.ID
        WHERE pnm.ANIO_REGISTRO = :year
        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%')
        AND p.TIPO_PERSONA = 'Estudiante'
        ORDER BY p.NOMBRES
    """)
    
    result = connection.execute(query, {"year": int(selected_year)})
    rows = result.fetchall()

if not rows:
    st.warning(f"⚠️ No hay datos para el año {selected_year}")
    st.stop()

df = pd.DataFrame(rows, columns=[
    'Identificación', 'Nombres', 'Apellidos', 'Sexo',
    'Nivel MCER', 'Grado', 'Año', 'Curso', 'Institución', 'Ciudad'
])

# Métricas
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("👥 Total Estudiantes", len(df))

with col2:
    femenino = len(df[df['Sexo'].str.lower() == 'f'])
    st.metric("👩 Mujeres", femenino)

with col3:
    masculino = len(df[df['Sexo'].str.lower() == 'm'])
    st.metric("👨 Hombres", masculino)

with col4:
    niveles = df['Nivel MCER'].nunique()
    st.metric("📈 Niveles MCER", niveles)

st.divider()

# Visualizaciones
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribución por Sexo")
    sex_dist = df['Sexo'].value_counts()
    sex_labels = ['Femenino' if x.lower() == 'f' else 'Masculino' if x.lower() == 'm' else x for x in sex_dist.index]
    fig_sex = px.pie(
        values=sex_dist.values,
        names=sex_labels,
        title=f"Estudiantes por Sexo - {selected_year}",
        color_discrete_sequence=['#FF69B4', '#4169E1']
    )
    st.plotly_chart(fig_sex, use_container_width=True)

with col2:
    st.subheader("Distribución por Nivel MCER")
    nivel_dist = df['Nivel MCER'].value_counts().sort_index()
    fig_nivel = px.bar(
        x=nivel_dist.index,
        y=nivel_dist.values,
        title=f"Estudiantes por Nivel MCER - {selected_year}",
        labels={'x': 'Nivel MCER', 'y': 'Cantidad'},
        color=nivel_dist.values,
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig_nivel, use_container_width=True)

st.subheader("📋 Datos Detallados")
st.dataframe(df, use_container_width=True)

# Descargar datos
col1, col2 = st.columns(2)
with col1:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"estudiantes_intensificacion_{selected_year}.csv",
        mime="text/csv"
    )

with col2:
    st.info(f"💡 Mostrando {len(df)} estudiantes de Formación Intensificación para el año {selected_year}")
