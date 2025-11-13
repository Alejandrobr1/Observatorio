import streamlit as stimport streamlit as st

import osimport pandas as pd

import pandas as pdimport plotly.express as px

from sqlalchemy import create_engine, textfrom sqlalchemy import create_engine, text

import plotly.express as pximport os



try:st.set_page_config(page_title="Sexo y Grado - Sábados", layout="wide", page_icon="👥")

    from dotenv import load_dotenv

    load_dotenv()st.title("👥 Sexo y Grado - Formación Sábados")

except ImportError:

    pass@st.cache_resource

def get_engine():

st.set_page_config(page_title="Sexo y Grado - Sábados", layout="wide", page_icon="👥")    try:

        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))

st.title("👥 Sexo y Grado - Formación Sábados")        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))

        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))

@st.cache_resource        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))

def get_engine():        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))

    try:    except FileNotFoundError:

        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))        db_user = os.getenv('DB_USER', 'root')

        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))        db_pass = os.getenv('DB_PASS', '123456')

        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))        db_host = os.getenv('DB_HOST', 'localhost')

        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))        db_port = os.getenv('DB_PORT', '3308')

        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')

    except FileNotFoundError:    

        db_user = os.getenv('DB_USER', 'root')    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        db_pass = os.getenv('DB_PASS', '123456')    return create_engine(connection_string)

        db_host = os.getenv('DB_HOST', 'localhost')

        db_port = os.getenv('DB_PORT', '3308')@st.cache_data

        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')def get_data_sexo_grado():

        engine = get_engine()

    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"    query = """

    return create_engine(connection_string)    SELECT 

        pnm.GRADO,

@st.cache_data        p.SEXO,

def get_data_sexo_grado():        COUNT(*) as cantidad,

    engine = get_engine()        pnm.ANIO_REGISTRO

    query = """    FROM Persona_Nivel_MCER pnm

    SELECT     JOIN Personas p ON pnm.PERSONA_ID = p.ID

        COALESCE(p.SEXO, 'SIN ESPECIFICAR') as sexo,    WHERE pnm.NOMBRE_CURSO LIKE '%Sabados%' OR pnm.NOMBRE_CURSO LIKE '%sabados%'

        COALESCE(p.GRADO, 'SIN ESPECIFICAR') as grado,    GROUP BY pnm.GRADO, p.SEXO, pnm.ANIO_REGISTRO

        COUNT(DISTINCT p.ID) as cantidad    ORDER BY pnm.GRADO, p.SEXO

    FROM Persona_Nivel_MCER pnm    """

    INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID    return pd.read_sql(text(query), engine)

    WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%sabados%'

    GROUP BY COALESCE(p.SEXO, 'SIN ESPECIFICAR'), COALESCE(p.GRADO, 'SIN ESPECIFICAR')try:

    ORDER BY cantidad DESC    df = get_data_sexo_grado()

    """    

    return pd.read_sql(text(query), engine)    col1, col2, col3 = st.columns(3)

    col1.metric("📊 Registros Total", len(df))

try:    col2.metric("👥 Sexos", df['SEXO'].nunique())

    df = get_data_sexo_grado()    col3.metric("🎓 Grados", df['GRADO'].nunique())

        

    col1, col2, col3 = st.columns(3)    st.divider()

    col1.metric("📊 Registros Total", df['cantidad'].sum())    

    col2.metric("👥 Sexos", df['sexo'].nunique())    # Gráfico de sexo y grado

    col3.metric("🎓 Grados", df['grado'].nunique())    sexo_grado = df.groupby(['GRADO', 'SEXO'])['cantidad'].sum().reset_index()

        

    st.divider()    fig1 = px.bar(

            sexo_grado,

    # Gráfico de sexo y grado        x='GRADO',

    fig1 = px.bar(        y='cantidad',

        df,        color='SEXO',

        x='grado',        barmode='group',

        y='cantidad',        title='Distribución por Grado y Sexo',

        color='sexo',        labels={'cantidad': 'Cantidad', 'GRADO': 'Grado', 'SEXO': 'Sexo'}

        barmode='group',    )

        title='Distribución por Grado y Sexo',    

        labels={'cantidad': 'Cantidad', 'grado': 'Grado', 'sexo': 'Sexo'}    st.plotly_chart(fig1, use_container_width=True)

    )    

        # Tabla de datos

    st.plotly_chart(fig1, use_container_width=True)    st.subheader("📋 Datos detallados")

        st.dataframe(df, use_container_width=True)

    # Tabla de datos

    st.subheader("📋 Datos detallados")except Exception as e:

    st.dataframe(df, use_container_width=True)    st.error(f"Error al cargar datos: {e}")


except Exception as e:
    st.error(f"Error al cargar datos: {e}")
