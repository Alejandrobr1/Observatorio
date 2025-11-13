import streamlit as stimport streamlit as st

import pandas as pdimport pandas as pd

import plotly.express as pximport plotly.express as px

from sqlalchemy import create_engine, textfrom sqlalchemy import create_engine, text

import osimport os



st.set_page_config(page_title="Estudiantes Sábados", layout="wide", page_icon="📊")st.set_page_config(page_title="Estudiantes Sábados", layout="wide", page_icon="📊")



st.title("📊 Estudiantes - Formación Sábados")st.title("📊 Estudiantes - Formación Sábados")



@st.cache_resource@st.cache_resource

def get_engine():def get_engine():

    try:    # Primero intenta obtener de st.secrets (Streamlit Cloud)

        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))    # Si no está disponible, usa variables de entorno

        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))    try:

        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))

        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))

        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))

    except FileNotFoundError:        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))

        db_user = os.getenv('DB_USER', 'root')        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))

        db_pass = os.getenv('DB_PASS', '123456')    except FileNotFoundError:

        db_host = os.getenv('DB_HOST', 'localhost')        # Si secrets.toml no existe, usa solo variables de entorno

        db_port = os.getenv('DB_PORT', '3308')        db_user = os.getenv('DB_USER', 'root')

        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')        db_pass = os.getenv('DB_PASS', '123456')

            db_host = os.getenv('DB_HOST', 'localhost')

    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"        db_port = os.getenv('DB_PORT', '3308')

    return create_engine(connection_string)        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')

    

@st.cache_data    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

def get_estudiantes_sabados():    return create_engine(connection_string)

    engine = get_engine()

    query = """@st.cache_data

    SELECT def get_estudiantes_sabados():

        p.NOMBRES,    engine = get_engine()

        p.APELLIDOS,    query = """

        p.SEXO,    SELECT 

        nm.NIVEL_MCER,        p.NOMBRES,

        p.GRADO,        p.APELLIDOS,

        pnm.ANIO_REGISTRO,        p.SEXO,

        pnm.NOMBRE_CURSO,        nm.NIVEL_MCER,

        i.NOMBRE_INSTITUCION,        p.GRADO,

        ci.NOMBRE_CIUDAD,        pnm.ANIO_REGISTRO,

        p.TIPO_POBLACION        pnm.NOMBRE_CURSO,

    FROM Persona_Nivel_MCER pnm        i.NOMBRE_INSTITUCION,

    JOIN Personas p ON pnm.PERSONA_ID = p.ID        ci.NOMBRE_CIUDAD,

    JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID        p.TIPO_POBLACION

    JOIN Instituciones i ON nm.INSTITUCION_ID = i.ID    FROM Persona_Nivel_MCER pnm

    JOIN Ciudades ci ON i.CIUDAD_ID = ci.ID    JOIN Personas p ON pnm.PERSONA_ID = p.ID

    WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%sabados%'    JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID

    ORDER BY pnm.ANIO_REGISTRO DESC, p.NOMBRES    JOIN Instituciones i ON nm.INSTITUCION_ID = i.ID

    """    JOIN Ciudades ci ON i.CIUDAD_ID = ci.ID

    return pd.read_sql(text(query), engine)    WHERE LOWER(pnm.NOMBRE_CURSO) LIKE '%sabados%'

    ORDER BY pnm.ANIO_REGISTRO DESC, p.NOMBRES

try:    """

    df = get_estudiantes_sabados()    return pd.read_sql(text(query), engine)

    

    col1, col2, col3, col4 = st.columns(4)try:

    col1.metric("👥 Total Estudiantes", len(df))    df = get_estudiantes_sabados()

    col2.metric("📅 Años", df['ANIO_REGISTRO'].nunique())    

    col3.metric("🎓 Niveles", df['NIVEL_MCER'].nunique())    col1, col2, col3, col4 = st.columns(4)

    col4.metric("🏫 Instituciones", df['NOMBRE_INSTITUCION'].nunique())    col1.metric("👥 Total Estudiantes", len(df))

        col2.metric("📅 Años", df['ANIO_REGISTRO'].nunique())

    st.divider()    col3.metric("🎓 Niveles", df['NIVEL_MCER'].nunique())

        col4.metric("🏫 Instituciones", df['NOMBRE_INSTITUCION'].nunique())

    tab1, tab2, tab3, tab4 = st.tabs(["Distribución", "Por Año", "Por Institución", "Datos"])    

        st.divider()

    with tab1:    

        col1, col2 = st.columns(2)    tab1, tab2, tab3, tab4 = st.tabs(["Distribución", "Por Año", "Por Institución", "Datos"])

        with col1:    

            fig = px.pie(    with tab1:

                df.groupby('NIVEL_MCER').size().reset_index(name='count'),        col1, col2 = st.columns(2)

                names='NIVEL_MCER',        with col1:

                values='count',            fig = px.pie(

                title='Distribución por Nivel MCER'                df.groupby('NIVEL_MCER').size().reset_index(name='count'),

            )                names='NIVEL_MCER',

            st.plotly_chart(fig, use_container_width=True)                values='count',

                        title='Distribución por Nivel MCER'

        with col2:            )

            fig = px.pie(            st.plotly_chart(fig, use_container_width=True)

                df.groupby('SEXO').size().reset_index(name='count'),        

                names='SEXO',        with col2:

                values='count',            fig = px.pie(

                title='Distribución por Sexo'                df.groupby('SEXO').size().reset_index(name='count'),

            )                names='SEXO',

            st.plotly_chart(fig, use_container_width=True)                values='count',

                    title='Distribución por Sexo'

    with tab2:            )

        fig = px.bar(            st.plotly_chart(fig, use_container_width=True)

            df.groupby('ANIO_REGISTRO').size().reset_index(name='count'),    

            x='ANIO_REGISTRO',    with tab2:

            y='count',        fig = px.bar(

            title='Estudiantes por Año',            df.groupby('ANIO_REGISTRO').size().reset_index(name='count'),

            labels={'count': 'Cantidad', 'ANIO_REGISTRO': 'Año'}            x='ANIO_REGISTRO',

        )            y='count',

        st.plotly_chart(fig, use_container_width=True)            title='Estudiantes por Año',

                labels={'count': 'Cantidad', 'ANIO_REGISTRO': 'Año'}

    with tab3:        )

        inst_data = df.groupby('NOMBRE_INSTITUCION').size().reset_index(name='count').sort_values('count', ascending=False)        st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(    

            inst_data,    with tab3:

            y='NOMBRE_INSTITUCION',        inst_data = df.groupby('NOMBRE_INSTITUCION').size().reset_index(name='count').sort_values('count', ascending=False)

            x='count',        fig = px.bar(

            title='Estudiantes por Institución',            inst_data,

            labels={'count': 'Cantidad', 'NOMBRE_INSTITUCION': 'Institución'},            y='NOMBRE_INSTITUCION',

            orientation='h'            x='count',

        )            title='Estudiantes por Institución',

        st.plotly_chart(fig, use_container_width=True)            labels={'count': 'Cantidad', 'NOMBRE_INSTITUCION': 'Institución'},

                orientation='h'

    with tab4:        )

        st.dataframe(df, use_container_width=True)        st.plotly_chart(fig, use_container_width=True)

    

except Exception as e:    with tab4:

    st.error(f"Error al cargar datos: {e}")        st.dataframe(df, use_container_width=True)


except Exception as e:
    st.error(f"Error al cargar datos: {e}")
