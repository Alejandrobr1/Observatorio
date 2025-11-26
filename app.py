"""
Observatorio de Bilingüismo - Punto de Entrada Principal
Este archivo es el punto de entrada para Streamlit Cloud
"""
import streamlit as st
import io
import zipfile
import pandas as pd
from sqlalchemy import text, inspect
import os
import sys

# Añadir el directorio raíz del proyecto a sys.path para encontrar 'Base_datos'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from Base_datos.conexion import get_engine


# Configuración de la página
st.set_page_config(
    page_title="Observatorio Bilinguismo - Panel Principal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Estilos personalizados
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .dashboard-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
        border-left: 5px solid #667eea;
    }
    .section-title {
        font-size: 24px;
        font-weight: bold;
        color: #667eea;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


st.markdown(
    """<div class="main-header">
    <h1>📊 Observatorio de Bilingüismo</h1>
    <p>Sistema de Monitoreo y Análisis de Programas Educativos</p>
    </div>""",
    unsafe_allow_html=True
)


def export_all_tables_to_zip(engine):
    """Exporta todas las tablas de la base de datos a un ZIP con CSVs."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()


    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for table in tables:
            try:
                df = pd.read_sql(text(f"SELECT * FROM `{table}`"), engine)
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                zf.writestr(f"{table}.csv", csv_bytes)
            except Exception as e:
                st.warning(f"No se pudo exportar la tabla {table}: {e}")
                continue


    mem_zip.seek(0)
    return mem_zip.read()


# Contenido principal
tab1, tab2, tab3 = st.tabs(["🏠 Inicio", "📈 Dashboards", "📥 Descargas"])


with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Acerca del Observatorio")
        st.markdown("""
        Este sistema permite monitorear y analizar los programas educativos de bilingüismo
        con datos actualizados desde 2016.
        
        **Características:**
        - 📊 Múltiples dashboards analíticos
        - 👥 Análisis de estudiantes y docentes
        - 🏫 Estadísticas por institución
        - 💾 Exportación de datos completos
        """)
    
    with col2:
        try:
            engine = get_engine()
            with engine.connect() as conn:
                # Contar registros
                personas_result = conn.execute(text("SELECT COUNT(*) as total FROM Personas"))
                personas_count = personas_result.fetchone()[0]
                
                inst_result = conn.execute(text("SELECT COUNT(*) as total FROM Instituciones"))
                inst_count = inst_result.fetchone()[0]
                
            col2.metric("👥 Total de Personas", personas_count)
            col2.metric("🏫 Instituciones", inst_count)
        except Exception as e:
            st.warning(f"No se pudo conectar a la base de datos: {e}")


with tab2:
    st.markdown("### 📈 Dashboards Disponibles")
    st.markdown("""
    Haz clic en cualquier dashboard para acceder a análisis específicos sobre los programas educativos.
    """)
    st.markdown("---")
    
    # Nueva sección para los dashboards de producción
    st.markdown("#### 📊 Análisis de Matrículas")
    
    st.page_link("pages/1p-estudiantes_por_sede_nodal_consolidado.py", label="Matriculados por Sede Nodal (2016-2019)", icon="🏫")
    # st.page_link("pages/2p-estudiantes_por_jornada_dia_2016.py", label="Matriculados por Jornada y Día", icon="📅")
    # st.page_link("pages/3p-estudiantes_por_poblacion_2016.py", label="Matriculados por Población", icon="👥")
    
    st.divider()

    # Nueva sección para los dashboards de Colombo
    st.markdown("#### 🇨🇴 Análisis Colombo Americano")
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/11p-colombo_por_institucion.py", label="Colombo - Estudiantes por Institución", icon="🏫")
        st.page_link("pages/12p-colombo_por_nivel.py", label="Colombo - Estudiantes por Nivel", icon="📈")
    
    st.info("💡 Los dashboards también están disponibles en el menú sidebar de Streamlit (esquina superior izquierda)")


with tab3:
    st.markdown("### 📥 Centro de Descargas")
    
    st.markdown("#### Exportar Base de Datos Completa")
    st.markdown("Descarga un ZIP con todos los datos de cada tabla en formato CSV.")
    
    if st.button("📦 Generar ZIP con todas las tablas", key="export_zip"):
        with st.spinner("Generando exportación..."):
            try:
                engine = get_engine()
                data_bytes = export_all_tables_to_zip(engine)
                st.download_button(
                    label="⬇️ Descargar ZIP",
                    data=data_bytes,
                    file_name="observatorio_bilinguismo_completo.zip",
                    mime="application/zip"
                )
                st.success("✅ Exportación lista para descargar")
            except Exception as e:
                st.error(f"Error al exportar: {e}")


st.sidebar.markdown("---")
st.sidebar.markdown("### Programa Municipal de Bilingüismo")
st.sidebar.markdown("""
**Observatorio de Bilingüismo**
- Versión: 1.0
- Última actualización: 2025
- El programa de bilingüismo busca fortalecer 
    las competencias comunicativas en inglés de 
    los estudiantes del municipio, promoviendo 
    una educación inclusiva y de calidad.
""")
