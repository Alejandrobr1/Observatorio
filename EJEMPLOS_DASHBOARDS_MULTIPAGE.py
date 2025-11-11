"""
GUÍA: Cómo agregar más dashboards a la estructura multipage de Streamlit

Streamlit automáticamente detecta archivos en la carpeta 'pages/' y los convierte
en páginas accesibles desde el menú lateral.

CONVENCIÓN DE NOMBRES:
- Comienza con número (01_, 02_, etc.) para controlar el orden
- Usa emojis para hacer visibles los títulos
- Formato: {numero}_{emoji}_{nombre}.py
"""

# ============================================================================
# EJEMPLO 1: Dashboard simple de Formación Docentes
# ============================================================================
# Archivo: pages/3_📊_Estudiantes_Docentes.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import os

st.set_page_config(page_title="Estudiantes Docentes", layout="wide", page_icon="📊")

st.title("📊 Estudiantes - Formación Docentes")

@st.cache_resource
def get_engine():
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '123456')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3308')
    db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

@st.cache_data
def get_estudiantes_docentes():
    engine = get_engine()
    query = """
    SELECT 
        p.NOMBRES,
        p.APELLIDOS,
        p.SEXO,
        pnm.NIVEL_MCER,
        pnm.GRADO,
        pnm.ANIO_REGISTRO,
        i.NOMBRE_INSTITUCION
    FROM Persona_Nivel_MCER pnm
    JOIN Personas p ON pnm.PERSONA_ID = p.ID
    JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID
    JOIN Instituciones i ON nm.INSTITUCION_ID = i.ID
    WHERE pnm.NOMBRE_CURSO LIKE '%Docente%' OR pnm.NOMBRE_CURSO LIKE '%docente%'
    ORDER BY pnm.ANIO_REGISTRO DESC, p.NOMBRES
    """
    return pd.read_sql(text(query), engine)

try:
    df = get_estudiantes_docentes()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Estudiantes", len(df))
    col2.metric("📅 Años", df['ANIO_REGISTRO'].nunique())
    col3.metric("🎓 Niveles", df['NIVEL_MCER'].nunique())
    col4.metric("🏫 Instituciones", df['NOMBRE_INSTITUCION'].nunique())
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Visualización", "Datos"])
    
    with tab1:
        fig = px.bar(
            df.groupby('NIVEL_MCER').size().reset_index(name='count'),
            x='NIVEL_MCER',
            y='count',
            title='Distribución por Nivel MCER'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")


# ============================================================================
# EJEMPLO 2: Dashboard de Intensificación con filtros
# ============================================================================
# Archivo: pages/5_⚡_Estudiantes_Intensificacion.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import os

st.set_page_config(page_title="Intensificación", layout="wide", page_icon="⚡")

st.title("⚡ Programas de Intensificación")

@st.cache_resource
def get_engine():
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '123456')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3308')
    db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

@st.cache_data
def get_intensificacion_data():
    engine = get_engine()
    query = """
    SELECT 
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
    JOIN Personas p ON pnm.PERSONA_ID = p.ID
    JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID
    JOIN Instituciones i ON nm.INSTITUCION_ID = i.ID
    JOIN Ciudades ci ON i.CIUDAD_ID = ci.ID
    WHERE pnm.NOMBRE_CURSO LIKE '%Intensificacion%' OR pnm.NOMBRE_CURSO LIKE '%intensificacion%'
    ORDER BY pnm.ANIO_REGISTRO DESC, p.NOMBRES
    """
    return pd.read_sql(text(query), engine)

try:
    df = get_intensificacion_data()
    
    # Filtros en sidebar
    st.sidebar.header("Filtros")
    años = sorted(df['ANIO_REGISTRO'].unique())
    año_seleccionado = st.sidebar.multiselect("Año(s)", años, default=años[-1:])
    
    instituciones = sorted(df['NOMBRE_INSTITUCION'].unique())
    inst_seleccionada = st.sidebar.multiselect("Institución(es)", instituciones)
    
    # Aplicar filtros
    df_filtrado = df
    if año_seleccionado:
        df_filtrado = df_filtrado[df_filtrado['ANIO_REGISTRO'].isin(año_seleccionado)]
    if inst_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['NOMBRE_INSTITUCION'].isin(inst_seleccionada)]
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Estudiantes", len(df_filtrado))
    col2.metric("🎓 Niveles", df_filtrado['NIVEL_MCER'].nunique())
    col3.metric("🏫 Instituciones", df_filtrado['NOMBRE_INSTITUCION'].nunique())
    col4.metric("📍 Ciudades", df_filtrado['NOMBRE_CIUDAD'].nunique())
    
    st.divider()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.pie(
            df_filtrado.groupby('NIVEL_MCER').size().reset_index(name='count'),
            names='NIVEL_MCER',
            values='count',
            title='Por Nivel MCER'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.bar(
            df_filtrado.groupby('NOMBRE_INSTITUCION').size().reset_index(name='count').sort_values('count', ascending=False),
            x='count',
            y='NOMBRE_INSTITUCION',
            title='Por Institución',
            orientation='h'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabla de datos
    st.subheader("📋 Datos Detallados")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")


# ============================================================================
# EJEMPLO 3: Dashboard de Estado/Certificación con gráficos avanzados
# ============================================================================
# Archivo: pages/6_🎓_Estado_Certificacion.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import os

st.set_page_config(page_title="Estado Certificación", layout="wide", page_icon="🎓")

st.title("🎓 Estado de Certificación")

@st.cache_resource
def get_engine():
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '123456')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3308')
    db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

@st.cache_data
def get_certificacion_data():
    engine = get_engine()
    query = """
    SELECT 
        nm.CERTIFICADO,
        COUNT(*) as cantidad,
        pnm.NIVEL_MCER
    FROM Persona_Nivel_MCER pnm
    JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID
    GROUP BY nm.CERTIFICADO, pnm.NIVEL_MCER
    """
    return pd.read_sql(text(query), engine)

try:
    df = get_certificacion_data()
    
    # Crear gráfico de treemap
    fig = go.Figure(go.Treemap(
        labels=df['NIVEL_MCER'] + ' - ' + df['CERTIFICADO'].astype(str),
        parents=[''] * len(df),
        values=df['cantidad'],
        marker=dict(
            colors=df['cantidad'],
            colorscale='RdYlGn',
            showscale=True
        )
    ))
    
    fig.update_layout(
        title="Distribución de Certificación por Nivel MCER",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla resumen
    st.subheader("Resumen")
    st.dataframe(df.sort_values('cantidad', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")


# ============================================================================
# CONSEJOS PARA CREAR DASHBOARDS
# ============================================================================

"""
PASOS PARA AGREGAR NUEVOS DASHBOARDS:

1. Crea un archivo en la carpeta 'pages/' con el nombre:
   {numero}_{emoji}_{nombre_dashboard}.py

2. Estructura básica del archivo:
   - Importar librerías necesarias
   - Configurar página: st.set_page_config()
   - Título: st.title()
   - Funciones con @st.cache_resource y @st.cache_data
   - Lógica principal con try/except

3. Usa estos decoradores:
   - @st.cache_resource: Para conexiones a BD (se mantienen entre reloads)
   - @st.cache_data: Para queries (se cachean los resultados)

4. Elementos útiles:
   - st.metric(): Mostrar números importantes
   - st.columns(): Crear columnas para layout
   - st.tabs(): Organizar contenido en pestañas
   - st.dataframe(): Mostrar tablas interactivas
   - plotly.express: Crear gráficos bonitos

5. Filtros:
   - st.sidebar.selectbox(): Dropdown
   - st.sidebar.multiselect(): Selección múltiple
   - st.sidebar.slider(): Rango

6. Buenas prácticas:
   ✓ Cachea queries con @st.cache_data
   ✓ Maneja excepciones con try/except
   ✓ Usa st.spinner() para procesos largos
   ✓ Agrega filtros útiles en el sidebar
   ✓ Documenta el código con comentarios
   ✓ Usa variables de entorno para credenciales
"""

# ============================================================================
# PARA TESTEAR LOCALMENTE:
# ============================================================================

"""
Ejecuta en terminal:

    streamlit run Dashboards/main_dashboard.py

Esto abrirá el navegador con la aplicación y acceso a todos los dashboards
en el menú lateral.
"""
