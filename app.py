"""
Observatorio de Bilingüismo - Punto de Entrada Principal
Este archivo es el punto de entrada para Streamlit Cloud
"""
import streamlit as st
import io
import zipfile
import pandas as pd
from sqlalchemy import create_engine, text, inspect
import os

# Intenta cargar variables de entorno (funciona en desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Si no está instalado, continúa (Streamlit Cloud usa secrets)
    pass

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
        ORDER BY p.NÚMERO_DE_IDENTIFICACIÓN, pnm.ANIO_REGISTRO
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
    
    # Formación Sábados
    st.markdown("#### 📚 Formación Sábados (6 Dashboards)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("[📊 Estudiantes](/1_%F0%9F%93%8A_Estudiantes_Sabados)")
        st.markdown("[📊 Estado](/6_%F0%9F%93%8A_Estado_Estudiantes_Sabados)")
    with col2:
        st.markdown("[👥 Sexo y Grado](/2_%F0%9F%91%A5_Sexo_Grado_Sabados)")
        st.markdown("[📚 Niveles MCER](/8_%F0%9F%93%9A_Niveles_MCER_Sabados)")
    with col3:
        st.markdown("[🏫 Instituciones](/10_%F0%9F%8F%AB_Instituciones_Sabados)")
        st.markdown("[📍 Asistencia x Institución](/14_%F0%9F%93%9A_Asistencia_Institucion_Sabados)")
    st.divider()
    
    # Formación Docentes
    st.markdown("#### 🎓 Formación Docentes (2 Dashboards)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("[👥 Sexo y Grado](/3_%F0%9F%91%A5_Sexo_Grado_Docentes)")
    with col2:
        st.markdown("[📍 Asistencia x Institución](/12_%F0%9F%8F%AB_Asistencia_Institucion_Docentes)")
    st.divider()
    
    # Formación Intensificación
    st.markdown("#### ⚡ Formación Intensificación (6 Dashboards)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("[⚡ Estudiantes](/4_%F0%9F%93%8A_Estudiantes_Intensificacion)")
        st.markdown("[⚡ Estado](/7_%E2%9A%A1_Estado_Estudiantes_Intensificacion)")
    with col2:
        st.markdown("[📊 Sexo y Grado](/5_%F0%9F%93%88_Sexo_Grado_Intensificacion)")
        st.markdown("[📚 Niveles MCER](/9_%F0%9F%93%9A_Niveles_MCER_Intensificacion)")
    with col3:
        st.markdown("[🏫 Instituciones](/11_%F0%9F%8F%AB_Instituciones_Intensificacion)")
        st.markdown("[📍 Asistencia x Institución](/13_%E2%9A%A1_Asistencia_Institucion_Intensificacion)")
    st.divider()
    
    st.info("💡 Los dashboards también están disponibles en el menú sidebar de Streamlit (esquina superior izquierda)")

with tab3:
    st.markdown("### 📥 Centro de Descargas")
    
    col1, col2 = st.columns(2)
    
    with col1:
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
- [Documentación](https://github.com/observatorio)
""")
