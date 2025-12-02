import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import sys
import os
from dashboard_config import create_nav_buttons, get_current_page_category
from dashboard_config import COMFENALCO_LABEL
# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Estudiantes por Nivel MCER Intensificación")
st.title("📊 Estudiantes por Nivel MCER Intensificación")

# --- State and Navigation ---
if 'population_filter' not in st.session_state:
    st.session_state.population_filter = COMFENALCO_LABEL

create_nav_buttons(st.session_state.population_filter)
st.markdown("---")
st.markdown("""
<style>
    /* Style for page links with flexible height and text wrapping */
    a[data-testid="stPageLink"] {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px 10px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        min-height: 5.5em;
        line-height: 1.4;
        word-wrap: break-word;
        white-space: normal;
        font-size: 0.85em;
        overflow-wrap: break-word;
        word-break: break-word;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_engine():
    # Lee desde st.secrets
    db_user = st.secrets["DB_USER"]
    db_pass = st.secrets["DB_PASS"]
    db_host = st.secrets["DB_HOST"]
    db_port = st.secrets["DB_PORT"]
    db_name = st.secrets["DB_NAME"]
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string, pool_pre_ping=True)

# Inicializar conexión
try:
    engine = get_engine()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

@st.cache_data
def get_available_years(_engine):
    table_name = "Estudiantes_intensificacion"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return []
        query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} ORDER BY FECHA DESC")
        years = [row[0] for row in connection.execute(query_years).fetchall()]
        return years

def create_mcer_donut_chart(df_data, total_estudiantes, title):
    """Función para crear un gráfico de dona y una tabla para estudiantes por Nivel MCER."""
    st.header(f"📊 {title} - Año {st.session_state.selected_year}")

    if df_data.empty:
        st.warning("No hay datos de estudiantes por Nivel MCER para el año seleccionado.")
        return

    # Gráfico de dona
    st.subheader("Visualización de Porcentajes")
    fig, ax = plt.subplots(figsize=(8, 6))
    
    labels = df_data['nivel_mcer']
    sizes = df_data['cantidad']
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(labels)))
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                      colors=colors, pctdistance=0.85,
                                      wedgeprops=dict(width=0.4, edgecolor='w'))
    
    plt.setp(autotexts, size=10, weight="bold", color="white")
    ax.set_title("Distribución de Estudiantes por Nivel MCER", pad=20)
    
    centre_circle = plt.Circle((0,0),0.60,fc='white')
    fig.gca().add_artist(centre_circle)
    
    ax.axis('equal')
    plt.tight_layout()
    st.pyplot(fig)

    # Tabla de resumen
    st.subheader("📋 Resumen por Nivel MCER")
    df_data['porcentaje'] = (df_data['cantidad'] / float(total_estudiantes) * 100) if total_estudiantes > 0 else 0
    df_display = df_data.copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
    df_display = df_display[['#', 'nivel_mcer', 'cantidad', 'porcentaje']]
    df_display.columns = ['#', 'Nivel MCER', 'Estudiantes', 'Porcentaje']
    st.dataframe(df_display, use_container_width=True, hide_index=True)

@st.cache_data
def load_data_by_mcer(_engine, year):
    """Cargar cantidad de estudiantes agrupados por Nivel MCER."""
    table_name = "Estudiantes_intensificacion"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(), 0, 0
        
        params = {'year': year}
        query_data = text(f"""
            SELECT 
                NIVEL_MCER as nivel_mcer, COUNT(ID) as cantidad
            FROM {table_name}
            WHERE FECHA = :year
              AND NIVEL_MCER IS NOT NULL 
              AND NIVEL_MCER != '' 
              AND NIVEL_MCER != 'SIN INFORMACION'
            GROUP BY nivel_mcer
            ORDER BY cantidad DESC
        """)
        df = pd.DataFrame(connection.execute(query_data, params).fetchall(), columns=["nivel_mcer", "cantidad"]) # type: ignore
        
        query_total = text(f"SELECT COUNT(ID) FROM {table_name} WHERE FECHA = :year")
        total_estudiantes = connection.execute(query_total, params).scalar() or 0
        
        total_niveles = df['nivel_mcer'].nunique() if not df.empty else 0
        
        return df, total_estudiantes, total_niveles

@st.cache_data
def get_institutions_by_mcer(_engine, year):
    """Obtener cantidad de instituciones por Nivel MCER."""
    table_name = "Estudiantes_intensificacion"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame()
        
        params = {'year': year}
        query_data = text(f"""
            SELECT 
                NIVEL_MCER as nivel_mcer, 
                COUNT(DISTINCT INSTITUCION_EDUCATIVA) as instituciones
            FROM {table_name}
            WHERE FECHA = :year
              AND NIVEL_MCER IS NOT NULL 
              AND NIVEL_MCER != '' 
              AND NIVEL_MCER != 'SIN INFORMACION'
              AND INSTITUCION_EDUCATIVA IS NOT NULL 
              AND INSTITUCION_EDUCATIVA != '' 
              AND INSTITUCION_EDUCATIVA != 'SIN INFORMACION'
            GROUP BY nivel_mcer
            ORDER BY instituciones DESC
        """)
        df = pd.DataFrame(connection.execute(query_data, params).fetchall(), columns=["nivel_mcer", "instituciones"]) # type: ignore
        return df

try:
    available_years = get_available_years(engine)
    if not available_years:
        st.warning(f"⚠️ No se encontraron datos en la tabla Estudiantes_intensificacion.")
        st.stop()

    if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
        st.session_state.selected_year = available_years[0]
    selected_year = st.session_state.selected_year

    # --- RENDERIZACIÓN DEL LAYOUT ---
    # Se define el layout principal ANTES de cargar los datos para que los filtros siempre estén visibles.
    col1, col2 = st.columns([3, 1])

    # Columna de filtros (siempre visible)
    with col2:
        st.write("📅 **Seleccionar Año**")
        def set_year(year):
            st.session_state.selected_year = year

        for year in available_years:
            button_type = "primary" if year == selected_year else "secondary"
            st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

    # --- CARGA DE DATOS Y RENDERIZACIÓN CONDICIONAL ---
    # Cargar los datos para el año seleccionado
    df_mcer, total_estudiantes, total_niveles = load_data_by_mcer(engine, selected_year)
    df_institutions = get_institutions_by_mcer(engine, selected_year)

    # Actualizar la barra lateral con las estadísticas
    st.sidebar.info(f"**Año:** {selected_year}")
    st.sidebar.divider()
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{int(total_estudiantes):,}")
    st.sidebar.metric(f"Niveles MCER ({selected_year})", f"{int(total_niveles):,}")
    st.sidebar.divider()
    
    if not df_institutions.empty:
        st.sidebar.subheader("🏫 Instituciones por Nivel")
        for _, row in df_institutions.iterrows():
            st.sidebar.write(f"**{row['nivel_mcer']}**: {int(row['instituciones'])} instituciones")
        st.sidebar.divider()
    
    if os.path.exists("assets/Logo_rionegro.png"):
        st.sidebar.image("assets/Logo_rionegro.png")

    # Columna de contenido (muestra advertencia o gráfico)
    with col1:
        if df_mcer.empty:
            st.warning(f"⚠️ No se encontraron datos para el año {selected_year}.")
        else:
            create_mcer_donut_chart(df_mcer, total_estudiantes, "Distribución de Estudiantes por Nivel MCER")

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)

def add_interest_links():
    st.markdown("---")
    st.markdown("### 🔗 Oportunidades laborales")
    st.markdown("""
    - [Agencia pública de empleo – Comfenalco Antioquia](https://www.comfenalcoantioquia.com.co/personas/sedes/oficina-de-empleo-oriente)
    - [Agencia Pública de Empleo Municipio de Rionegro](https://www.comfenalcoantioquia.com.co/personas/servicios/agencia-de-empleo/ofertas)
    - [Agencia Pública de Empleo SENA](https://ape.sena.edu.co/Paginas/Inicio.aspx) 
    """)
add_interest_links()
