import streamlit as st
import io
import zipfile
import pandas as pd
from sqlalchemy import create_engine, text, inspect
import os

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

# Obtener conexión a la base de datos
@st.cache_resource
def get_engine():
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '123456')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3308')
    db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

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

def export_combined_data(engine):
    """Exporta los datos principales combinados en un único CSV."""
    try:
        query = """
        SELECT 
            p.NÚMERO_DE_IDENTIFICACIÓN,
            p.NOMBRES,
            p.APELLIDOS,
            p.SEXO,
            pnm.NIVEL_MCER,
            pnm.GRADO,
            pnm.ANIO_REGISTRO,
            pnm.NOMBRE_CURSO,
            pnm.TIPO_POBLACION,
            i.NOMBRE_INSTITUCION,
            ci.NOMBRE_CIUDAD
        FROM Persona_Nivel_MCER pnm
        JOIN Personas p ON pnm.PERSONA_ID = p.ID
        JOIN Nivel_MCER nm ON pnm.NIVEL_MCER_ID = nm.ID
        JOIN Instituciones i ON nm.INSTITUCION_ID = i.ID
        JOIN Ciudades ci ON i.CIUDAD_ID = ci.ID
        ORDER BY p.NÚMEROS_DE_IDENTIFICACIÓN, pnm.ANIO_REGISTRO
        """
        df = pd.read_sql(text(query), engine)
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(f"Error al exportar datos combinados: {e}")
        return None

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
        - 📉 Seguimiento de niveles MCER
        - 💾 Exportación de datos completos
        """)
    
    with col2:
        try:
            engine = get_engine()
            with engine.connect() as conn:
                # Contar registros
                personas_result = conn.execute(text("SELECT COUNT(*) as total FROM Personas"))
                personas_count = personas_result.fetchone()[0]
                
                pnm_result = conn.execute(text("SELECT COUNT(*) as total FROM Persona_Nivel_MCER"))
                pnm_count = pnm_result.fetchone()[0]
                
                inst_result = conn.execute(text("SELECT COUNT(*) as total FROM Instituciones"))
                inst_count = inst_result.fetchone()[0]
                
            col2.metric("👥 Total de Personas", personas_count)
            col2.metric("📊 Registros Nivel MCER", pnm_count)
            col2.metric("🏫 Instituciones", inst_count)
        except Exception as e:
            st.warning(f"No se pudo conectar a la base de datos: {e}")

with tab2:
    st.markdown("### 📈 Dashboards Disponibles")
    st.markdown("""
    Haz clic en cualquier dashboard para acceder a análisis específicos sobre los programas educativos.
    """)
    st.markdown("")
    
    # Dashboard 1: Estudiantes Sábados
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown("#### 📊 Estudiantes Sábados")
        st.markdown("Análisis detallado de estudiantes en programas de Formación Sábados")
    with col2:
        pass
    with col3:
        if st.button("Abrir →", key="btn_dashboard_1", use_container_width=True):
            st.switch_page("pages/1_📊_Estudiantes_Sabados.py")
    st.divider()
    
    # Dashboard 2: Sexo/Grado Sábados
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown("#### 👥 Sexo y Grado - Sábados")
        st.markdown("Análisis de distribución por sexo y nivel de grado en Formación Sábados")
    with col2:
        pass
    with col3:
        if st.button("Abrir →", key="btn_dashboard_2", use_container_width=True):
            st.switch_page("pages/2_👥_Sexo_Grado_Sabados.py")
    st.divider()
    
    st.info("💡 Más dashboards serán agregados próximamente")

with tab3:
    st.markdown("### 📥 Centro de Descargas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Exportar Base de Datos Completa")
        st.markdown("Descarga un ZIP con todos los datos de cada tabla en formato CSV.")
        
        if st.button("� Generar ZIP con todas las tablas", key="export_zip"):
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
    
    with col2:
        st.markdown("#### Exportar Datos Combinados")
        st.markdown("Descarga un CSV con los datos principales de estudiantes y niveles.")
        
        if st.button("📄 Generar CSV combinado", key="export_csv"):
            with st.spinner("Generando exportación..."):
                try:
                    engine = get_engine()
                    data_bytes = export_combined_data(engine)
                    if data_bytes:
                        st.download_button(
                            label="⬇️ Descargar CSV",
                            data=data_bytes,
                            file_name="observatorio_bilinguismo_datos.csv",
                            mime="text/csv"
                        )
                        st.success("✅ Exportación lista para descargar")
                except Exception as e:
                    st.error(f"Error al exportar: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información")
st.sidebar.markdown("""
**Observatorio de Bilingüismo**
- Versión: 1.0
- Última actualización: 2025
- [Contacto](mailto:info@observatorio.edu)
""")
