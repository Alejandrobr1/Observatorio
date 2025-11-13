import streamlit as st"""

import osDashboard: Estudiantes por Sexo y Grado - Formación Intensificación

import pandas as pd"""

from sqlalchemy import create_engine, textimport streamlit as st

import plotly.express as pximport os

import pandas as pd

st.set_page_config(page_title="Sexo y Grado - Intensificación", layout="wide", page_icon="📈")from sqlalchemy import create_engine, text

st.title("📈 Sexo y Grado - Formación Intensificación")import plotly.express as px



@st.cache_resource# Intenta cargar variables de entorno (funciona en desarrollo local)

def get_engine():try:

    try:    from dotenv import load_dotenv

        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))    load_dotenv()

        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))except ImportError:

        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))    # Si no está instalado, continúa (Streamlit Cloud usa secrets)

        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))    pass

        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))

    except FileNotFoundError:st.set_page_config(page_title="Sexo y Grado - Intensificación", layout="wide", page_icon="📊")

        db_user = os.getenv('DB_USER', 'root')

        db_pass = os.getenv('DB_PASS', '123456')st.title("📊 Distribución por Sexo y Grado - Formación Intensificación")

        db_host = os.getenv('DB_HOST', 'localhost')

        db_port = os.getenv('DB_PORT', '3308')@st.cache_resource

        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')def get_engine():

    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"    # Primero intenta obtener de st.secrets (Streamlit Cloud)

    return create_engine(connection_string)    # Si no está disponible, usa variables de entorno

    try:

try:        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))

    engine = get_engine()        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))

    with engine.connect() as conn:        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))

        conn.execute(text("SELECT 1"))        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))

    st.sidebar.success("✅ Conexión")        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))

except Exception as e:    except FileNotFoundError:

    st.error(f"Error: {e}")        # Si secrets.toml no existe, usa solo variables de entorno

    st.stop()        db_user = os.getenv('DB_USER', 'root')

        db_pass = os.getenv('DB_PASS', '123456')

st.sidebar.header("Filtros")        db_host = os.getenv('DB_HOST', 'localhost')

with engine.connect() as conn:        db_port = os.getenv('DB_PORT', '3308')

    query = text("""SELECT DISTINCT pnm.ANIO_REGISTRO FROM Persona_Nivel_MCER pnm         db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')

                    WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%' ORDER BY pnm.ANIO_REGISTRO DESC""")    

    years = [str(int(row[0])) for row in conn.execute(query).fetchall() if row[0]]    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    if not years:    return create_engine(connection_string)

        st.stop()

    selected_year = st.sidebar.selectbox('Año', years, index=0)try:

    engine = get_engine()

with engine.connect() as conn:    with engine.connect() as conn:

    query = text("""SELECT COALESCE(p.SEXO, 'N/A') as sexo, COALESCE(p.GRADO, 'N/A') as grado, COUNT(DISTINCT p.ID) as qty        conn.execute(text("SELECT 1"))

                    FROM Persona_Nivel_MCER pnm JOIN Personas p ON pnm.PERSONA_ID = p.ID    st.sidebar.success("✅ Conexión establecida")

                    WHERE pnm.ANIO_REGISTRO = :year AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%'except Exception as e:

                    GROUP BY sexo, grado""")    st.error(f"❌ Error de conexión: {e}")

    data = conn.execute(query, {"year": int(selected_year)}).fetchall()    st.stop()



if data:st.sidebar.header("🔍 Filtros")

    df = pd.DataFrame(data, columns=['Sexo', 'Grado', 'Cantidad'])

    st.metric("Total", df['Cantidad'].sum())with engine.connect() as connection:

    st.divider()    # Obtener años disponibles

    fig = px.bar(df, x='Grado', y='Cantidad', color='Sexo', barmode='group')    query_years = text("""

    st.plotly_chart(fig, use_container_width=True)        SELECT DISTINCT pnm.ANIO_REGISTRO as año

    st.dataframe(df)        FROM Persona_Nivel_MCER pnm

else:        WHERE pnm.ANIO_REGISTRO IS NOT NULL

    st.warning("Sin datos")        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%')

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
            COALESCE(p.GRADO, 'SIN ESPECIFICAR') as grado,
            COUNT(DISTINCT p.ID) as cantidad
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :year
        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%intensif%')
        GROUP BY COALESCE(p.SEXO, 'SIN ESPECIFICAR'), COALESCE(p.GRADO, 'SIN ESPECIFICAR')
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
