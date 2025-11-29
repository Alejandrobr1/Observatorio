import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import sys
import os
from dashboard_config import create_nav_buttons, COMFENALCO_LABEL

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Estudiantes por Grado Intensificación")
st.title("📊 Estudiantes por Grado Intensificación")

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
def get_available_years(_engine, population):
    table_name = "Estudiantes_intensificacion"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            st.warning(f"La tabla '{table_name}' no existe. No se pueden cargar los años.")
            return []
        query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} WHERE POBLACION = :population ORDER BY FECHA DESC")
        params = {'population': population}
        years = [row[0] for row in connection.execute(query_years, params).fetchall()]
        if years:
            return years
    st.warning(f"No se encontraron años en la tabla '{table_name}'.")
    return []

def create_grade_donut_chart(df_data, total_estudiantes, title):
    """Función para crear un gráfico de dona y una tabla para estudiantes por grado."""
    st.header(f"📊 {title} - Año {st.session_state.selected_year}")

    if df_data.empty:
        st.warning("No hay datos de estudiantes por grado para el año seleccionado.")
        return

    # Gráfico de dona
    st.subheader("Visualización de Porcentajes")
    fig, ax = plt.subplots(figsize=(8, 6))
    
    labels = df_data['grado']
    sizes = df_data['cantidad']
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(labels)))
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                      colors=colors, pctdistance=0.85,
                                      wedgeprops=dict(width=0.4, edgecolor='w'))
    
    plt.setp(autotexts, size=10, weight="bold", color="white")
    ax.set_title("Distribución de Estudiantes por Grado", pad=20)
    
    centre_circle = plt.Circle((0,0),0.60,fc='white')
    fig.gca().add_artist(centre_circle)
    
    ax.axis('equal')
    plt.tight_layout()
    st.pyplot(fig)

    # Tabla de resumen
    st.subheader("📋 Resumen por Grado")
    df_data['porcentaje'] = (df_data['cantidad'] / float(total_estudiantes) * 100) if total_estudiantes > 0 else 0
    df_display = df_data.copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
    df_display = df_display[['#', 'grado', 'cantidad', 'porcentaje']]
    df_display.columns = ['#', 'Grado', 'Estudiantes', 'Porcentaje']
    st.dataframe(df_display, use_container_width=True, hide_index=True)

@st.cache_data
def load_data_by_grade(_engine, year, population):
    table_name = "Estudiantes_intensificacion"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(), 0
        
        params = {'year': year, 'population': population}
        query_data = text(f"""
            SELECT 
                GRADO as grado, COUNT(ID) as cantidad
            FROM {table_name}
            WHERE FECHA = :year
              AND POBLACION = :population
              AND GRADO IS NOT NULL 
              AND GRADO != '' 
              AND GRADO != 'SIN INFORMACION'
            GROUP BY grado
            ORDER BY grado ASC
        """)
        df = pd.DataFrame(connection.execute(query_data, params).fetchall(), columns=["grado", "cantidad"]) # type: ignore
        
        query_total = text(f"SELECT COUNT(ID) FROM {table_name} WHERE FECHA = :year AND POBLACION = :population")
        total_estudiantes = connection.execute(query_total, params).scalar() or 0
        
        total_grados = df['grado'].nunique()
        
        return df, total_estudiantes, total_grados

try:
    available_years = get_available_years(engine, st.session_state.population_filter)
    if not available_years:
        st.warning(f"⚠️ No se encontraron datos para la población seleccionada en la tabla Estudiantes_intensificacion.")
        st.stop()

    if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
        st.session_state.selected_year = available_years[0]
    selected_year = st.session_state.selected_year

    df_grados, total_estudiantes, total_grados = load_data_by_grade(engine, selected_year, st.session_state.population_filter)

    st.sidebar.info(f"**Año:** {selected_year}")
    st.sidebar.divider()
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{int(total_estudiantes):,}")
    st.sidebar.metric(f"Grados ({selected_year})", f"{int(total_grados):,}")
    st.sidebar.divider()
    if os.path.exists("assets/Logo_rionegro.png"):
        st.sidebar.image("assets/Logo_rionegro.png")

    # Layout en dos columnas: Gráfico a la izquierda, filtro de año a la derecha
    col1, col2 = st.columns([3, 1])

    with col1:
        # Mostrar el gráfico de estudiantes por grado
        create_grade_donut_chart(df_grados, total_estudiantes, "Distribución de Estudiantes por Grado")

    with col2:
        st.write("📅 **Seleccionar Año**")
        def set_year(year):
            st.session_state.selected_year = year

        for year in available_years:
            button_type = "primary" if year == selected_year else "secondary"
            st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)

def add_interest_links():
    st.markdown("---")
    st.markdown("### 🔗 Enlaces de Interés")
    st.markdown("""
    - [Agencia Pública de Empleo Municipio de Comfenalco](https://www.comfenalcoantioquia.com.co/personas/sedes/oficina-de-empleo-oriente)
    - [Agencia Pública de Empleo Municipio de Rionegro](https://www.comfenalcoantioquia.com.co/personas/servicios/agencia-de-empleo/ofertas)
    - [Agencia Pública de Empleo SENA](https://ape.sena.edu.co/Paginas/Inicio.aspx) 
    """)
add_interest_links()
