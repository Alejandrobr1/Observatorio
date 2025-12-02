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

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Importar desde la nueva estructura src/
from src.database.conexion import get_engine
from dashboard_config import COLOMBO_LABEL, COMFENALCO_LABEL

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
    /* Estilo para los botones de filtro de población para que tengan la misma altura */
    div[data-testid="stHorizontalBlock"] button {
        height: 4.5em; /* Ajusta esta altura según sea necesario */
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        line-height: 1.2; /* Mejora el espaciado del texto en varias líneas */
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
        # Añadir el logo
        logo_path = "assets/Logo_rionegro.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=250) # Ajusta el ancho según sea necesario

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
            # Si hay un error de conexión, no se muestran las métricas,
            # pero se evita mostrar un mensaje de error al usuario en esta sección.
            pass


with tab2:
    st.markdown("### 📈 Dashboards Disponibles")
    st.markdown("Selecciona el tipo de población para ver los dashboards correspondientes.")

    # Definir las etiquetas para los filtros de población
    COMFENALCO_LABEL = "Comfenalco Antioquia"
    DOCENTES_LABEL = "Formación a docentes"
    COLOMBO_LABEL = "Centro Colombo Americano Medellín"

    # Inicializar el estado de la sesión para el filtro de población
    if 'population_filter' not in st.session_state:
        st.session_state.population_filter = COMFENALCO_LABEL
    # Inicializar el estado de la sesión para las subcategorías
    if 'comfenalco_subcategory' not in st.session_state:
        st.session_state.comfenalco_subcategory = "Años 2016 al 2019"
    if 'colombo_subcategory' not in st.session_state:
        st.session_state.colombo_subcategory = "Formación a estudiantes"

    def set_population(pop_type):
        st.session_state.population_filter = pop_type

    # Crear botones para seleccionar la población
    pop_options = [COMFENALCO_LABEL, COLOMBO_LABEL]
    cols_pop = st.columns(len(pop_options))
    for i, pop in enumerate(pop_options):
        with cols_pop[i]:
            st.button(pop, key=f"pop_btn_{pop}", on_click=set_population, args=(pop,), use_container_width=True, type="primary" if st.session_state.population_filter == pop else "secondary")

    st.markdown("---")
    
    # Mostrar enlaces de dashboards según la población seleccionada
    if st.session_state.population_filter == COMFENALCO_LABEL:
        def set_comfenalco_sub(sub_category):
            st.session_state.comfenalco_subcategory = sub_category

        sub_categories = ["Años 2016 al 2019", "Años 2021 al 2025", "Intensificación lingüística"]
        cols_sub = st.columns(len(sub_categories))
        for i, sub in enumerate(sub_categories):
            with cols_sub[i]:
                st.button(sub, key=f"comfenalco_sub_{i}", on_click=set_comfenalco_sub, args=(sub,), use_container_width=True, type="primary" if st.session_state.comfenalco_subcategory == sub else "secondary")

        st.markdown("---")
        
        if st.session_state.comfenalco_subcategory == "Años 2016 al 2019":
            st.markdown("#### 📊 Dashboards del periodo 2016-2019")
            col1, col2 = st.columns(2)
            with col1:
                st.page_link("pages/1p-estudiantes_por_jornada_dia.py", label="Estudiantes por Jornada y día", icon="📅")
                st.page_link("pages/2p-estudiantes_por_poblacion.py", label="Estudiantes por Población", icon="👥")
                st.page_link("pages/5p-estudiantes_por_institucion.py", label="Estudiantes Escuela Nueva", icon="🏫")
            with col2:
                st.page_link("pages/3p-estudiantes_por_sede_nodal_etapa1_2.py", label="Participación % por Sede nodal", icon="⚖️")
                st.page_link("pages/4p-estudiantes_por_sede_nodal_barras_etp1_2.py", label="Estudiantes por Sede nodal", icon="📊")

        elif st.session_state.comfenalco_subcategory == "Años 2021 al 2025":
            st.markdown("#### 📊 Dashboards del periodo 2021-2025")
            col1, col2 = st.columns(2)
            with col1:
                st.page_link("pages/10p-estudiantes_por_institucion_2021_2025.py", label="Estudiantes por Institución Educativa", icon="🏫")
            with col2:
                st.page_link("pages/11p-estudiantes_por_grado_2021_2025.py", label="Estudiantes por Grado", icon="🎓")

        elif st.session_state.comfenalco_subcategory == "Intensificación lingüística":
            st.markdown("#### 📊 Dashboards de Intensificación Lingüística")
            col1, col2 = st.columns(2)
            with col1:
                st.page_link("pages/12p-estudiantes_por_institucion_intensificacion.py", label="Estudiantes por Institución", icon="🏫")
                st.page_link("pages/13p-estudiantes_por_grado_intensificacion.py", label="Estudiantes por Grado", icon="🎓")
            with col2:
                st.page_link("pages/14p-estudiantes_por_idioma_intensificacion.py", label="Estudiantes por Idioma", icon="📈")

    elif st.session_state.population_filter == COLOMBO_LABEL:
        def set_colombo_sub(sub_category):
            st.session_state.colombo_subcategory = sub_category

        sub_categories = ["Formación a estudiantes", "Formación a docentes"]
        cols_sub = st.columns(len(sub_categories))
        for i, sub in enumerate(sub_categories):
            with cols_sub[i]:
                st.button(sub, key=f"colombo_sub_{i}", on_click=set_colombo_sub, args=(sub,), use_container_width=True, type="secondary" if st.session_state.colombo_subcategory == sub else "secondary")

        st.markdown("---")

        if st.session_state.colombo_subcategory == "Formación a estudiantes":
            st.markdown("#### 📈 Dashboards de Formación a Estudiantes")
            col1, col2 = st.columns(2)
            with col1:
                st.page_link("pages/8p-colombo_por_institucion.py", label="Estudiantes por Institución Educativa", icon="🏫")
            with col2:
                st.page_link("pages/9p-colombo_por_nivel.py", label="Estudiantes por nivel MCER", icon="📈")

        elif st.session_state.colombo_subcategory == "Formación a docentes":
            st.markdown("#### 👨‍🏫 Dashboards de Formación a Docentes")
            col1, col2 = st.columns(2)
            with col1:
                st.page_link("pages/7p-docentes_por_institucion.py", label="Docentes por Institución Educativa", icon="🏫")
            with col2:
                st.page_link("pages/6p-docentes_por_nivel.py", label="Docentes por nivel MCER", icon="🎓")

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

def add_interest_links():
    st.markdown("---")
    st.markdown("### 🔗 Oportunidades laborales")
    st.markdown("""
    - [Agencia pública de empleo – Comfenalco Antioquia](https://www.comfenalcoantioquia.com.co/personas/sedes/oficina-de-empleo-oriente)
    - [Agencia Pública de Empleo Municipio de Rionegro](https://www.comfenalcoantioquia.com.co/personas/servicios/agencia-de-empleo/ofertas)
    - [Agencia Pública de Empleo SENA](https://ape.sena.edu.co/Paginas/Inicio.aspx) 
    """)
add_interest_links()
