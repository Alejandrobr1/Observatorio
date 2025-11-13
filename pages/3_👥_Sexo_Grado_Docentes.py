import streamlit as st"""

import osDashboard: Estudiantes por Sexo y Grado - Formación Docentes

import pandas as pd"""

from sqlalchemy import create_engine, textimport streamlit as st

import plotly.express as pximport os

import pandas as pd

try:from sqlalchemy import create_engine, text

    from dotenv import load_dotenvimport plotly.express as px

    load_dotenv()

except ImportError:# Intenta cargar variables de entorno (funciona en desarrollo local)

    passtry:

    from dotenv import load_dotenv

st.set_page_config(page_title="Sexo y Grado - Docentes", layout="wide", page_icon="👥")    load_dotenv()

except ImportError:

st.title("👥 Sexo y Grado - Formación Docentes")    # Si no está instalado, continúa (Streamlit Cloud usa secrets)

    pass

@st.cache_resource

def get_engine():st.set_page_config(page_title="Sexo y Grado - Docentes", layout="wide", page_icon="👥")

    try:

        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))st.title("👥 Distribución por Sexo y Grado - Formación Docentes")

        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))

        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))@st.cache_resource

        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))def get_engine():

        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))    # Primero intenta obtener de st.secrets (Streamlit Cloud)

    except FileNotFoundError:    # Si no está disponible, usa variables de entorno

        db_user = os.getenv('DB_USER', 'root')    try:

        db_pass = os.getenv('DB_PASS', '123456')        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))

        db_host = os.getenv('DB_HOST', 'localhost')        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))

        db_port = os.getenv('DB_PORT', '3308')        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))

        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))

            db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))

    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"    except FileNotFoundError:

    return create_engine(connection_string)        # Si secrets.toml no existe, usa solo variables de entorno

        db_user = os.getenv('DB_USER', 'root')

try:        db_pass = os.getenv('DB_PASS', '123456')

    engine = get_engine()        db_host = os.getenv('DB_HOST', 'localhost')

    with engine.connect() as conn:        db_port = os.getenv('DB_PORT', '3308')

        conn.execute(text("SELECT 1"))        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')

    st.sidebar.success("✅ Conexión establecida")    

except Exception as e:    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    st.error(f"❌ Error: {e}")    return create_engine(connection_string)

    st.stop()

try:

st.sidebar.header("🔍 Filtros")    engine = get_engine()

    with engine.connect() as conn:

with engine.connect() as connection:        conn.execute(text("SELECT 1"))

    query_years = text("""    st.sidebar.success("✅ Conexión establecida")

        SELECT DISTINCT pnm.ANIO_REGISTRO as añoexcept Exception as e:

        FROM Persona_Nivel_MCER pnm    st.error(f"❌ Error de conexión: {e}")

        WHERE pnm.ANIO_REGISTRO IS NOT NULL    st.stop()

        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%docente%'

        ORDER BY año DESCst.sidebar.header("🔍 Filtros")

    """)

    result_years = connection.execute(query_years)with engine.connect() as connection:

    available_years = [str(int(row[0])) for row in result_years.fetchall() if row[0]]    # Obtener años disponibles

    query_years = text("""

    if not available_years:        SELECT DISTINCT pnm.ANIO_REGISTRO as año

        st.warning("⚠️ No hay datos disponibles")        FROM Persona_Nivel_MCER pnm

        st.stop()        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID

        WHERE pnm.ANIO_REGISTRO IS NOT NULL

    selected_year = st.sidebar.selectbox('📅 Año', available_years, index=0)        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%docentes%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%docente%')

        AND p.TIPO_PERSONA = 'Estudiante'

    query = text("""        ORDER BY año DESC

        SELECT     """)

            COALESCE(p.SEXO, 'SIN ESPECIFICAR') as sexo,    result_years = connection.execute(query_years)

            COALESCE(p.GRADO, 'SIN ESPECIFICAR') as grado,    available_years = [str(int(row[0])) for row in result_years.fetchall() if row[0]]

            COUNT(DISTINCT p.ID) as cantidad

        FROM Persona_Nivel_MCER pnm    if not available_years:

        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID        st.warning("⚠️ No se encontraron datos para Formación Docentes")

        WHERE pnm.ANIO_REGISTRO = :year        st.info("Selecciona 'Sábados' en el menú lateral para ver otros dashboards")

        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%docente%'        st.stop()

        GROUP BY COALESCE(p.SEXO, 'SIN ESPECIFICAR'), COALESCE(p.GRADO, 'SIN ESPECIFICAR')

        ORDER BY cantidad DESC    selected_year = st.sidebar.selectbox('📅 Año', available_years, index=0)

    """)

        # Query principal

    result = connection.execute(query, {"year": int(selected_year)})    query = text("""

    data = result.fetchall()        SELECT 

            COALESCE(p.SEXO, 'SIN ESPECIFICAR') as sexo,

if data:            COALESCE(p.GRADO, 'SIN ESPECIFICAR') as grado,

    df = pd.DataFrame(data, columns=['Sexo', 'Grado', 'Cantidad'])            COUNT(DISTINCT p.ID) as cantidad

            FROM Persona_Nivel_MCER pnm

    col1, col2, col3 = st.columns(3)        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID

    with col1:        WHERE pnm.ANIO_REGISTRO = :year

        st.metric("👥 Total", df['Cantidad'].sum())        AND (LOWER(pnm.NOMBRE_CURSO) LIKE '%docentes%' OR LOWER(pnm.NOMBRE_CURSO) LIKE '%docente%')

    with col2:        GROUP BY COALESCE(p.SEXO, 'SIN ESPECIFICAR'), COALESCE(p.GRADO, 'SIN ESPECIFICAR')

        st.metric("👩 Femenino", df[df['Sexo'] == 'F']['Cantidad'].sum() if 'F' in df['Sexo'].values else 0)        ORDER BY cantidad DESC

    with col3:    """)

        st.metric("👨 Masculino", df[df['Sexo'] == 'M']['Cantidad'].sum() if 'M' in df['Sexo'].values else 0)    

        result = connection.execute(query, {"year": int(selected_year)})

    st.divider()    data = result.fetchall()

    

    col1, col2 = st.columns(2)if not data:

    with col1:    st.warning(f"⚠️ No hay datos para el año {selected_year}")

        fig = px.bar(df, x='grado', y='Cantidad', color='Sexo', title='Por Grado y Sexo', barmode='group')    st.stop()

        st.plotly_chart(fig, use_container_width=True)

    df = pd.DataFrame(data, columns=['Sexo', 'Grado', 'Cantidad'])

    with col2:

        fig = px.pie(df.groupby('Sexo')['Cantidad'].sum(), title='Distribución por Sexo')# Limpiar datos

        st.plotly_chart(fig, use_container_width=True)df['Sexo_Label'] = df['Sexo'].apply(lambda x: 'Femenino' if x.lower() == 'f' else ('Masculino' if x.lower() == 'm' else 'No especificado'))

    df['Grado'] = df['Grado'].fillna('Sin especificar')

    st.dataframe(df, use_container_width=True)

else:# Métricas

    st.warning(f"⚠️ Sin datos para {selected_year}")col1, col2, col3 = st.columns(3)

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

st.info("💡 Este dashboard muestra la distribución de estudiantes por sexo y grado en Formación Docentes")

