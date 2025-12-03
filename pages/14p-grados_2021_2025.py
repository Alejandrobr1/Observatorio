import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import sys
import os
from dashboard_config import create_nav_buttons
from dashboard_config import COMFENALCO_LABEL

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Grados por Etapa (2021-2025)")
st.title("📊 Grados y Matriculados por Etapa (2021-2025)")

# --- State and Navigation ---
if 'population_filter' not in st.session_state:
    st.session_state.population_filter = COMFENALCO_LABEL

create_nav_buttons(st.session_state.population_filter)
st.markdown('<hr class="compact">', unsafe_allow_html=True)
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
    table_name = "Grados_2021_2025"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            st.warning(f"La tabla '{table_name}' no existe. No se pueden cargar los años.")
            return []
        query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} ORDER BY FECHA DESC")
        years = [row[0] for row in connection.execute(query_years).fetchall()]
        if years:
            return years
    st.warning(f"No se encontraron años en la tabla '{table_name}'.")
    return []

def create_donut_chart_and_table(df_data, total_matriculados, title):
    """Función para crear un gráfico de dona y una tabla para una etapa."""
    st.header(title)

    if df_data.empty:
        st.warning("No hay datos de matriculados para esta etapa.")
        return

    # Gráfico de dona
    st.subheader("Distribución por Grado")
    fig, ax = plt.subplots(figsize=(8, 6))
    
    labels = df_data['grado']
    sizes = df_data['cantidad']
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(labels)))
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                      colors=colors, pctdistance=0.85,
                                      wedgeprops=dict(width=0.4, edgecolor='w'))
    
    plt.setp(autotexts, size=10, weight="bold", color="white")
    ax.set_title(f"Distribución de Matriculados - {title}", pad=20)
    
    centre_circle = plt.Circle((0,0),0.60,fc='white')
    fig.gca().add_artist(centre_circle)
    
    ax.axis('equal')
    plt.tight_layout()
    st.pyplot(fig)

    # Tabla de resumen
    st.subheader("📋 Resumen por Grado")
    df_data['porcentaje'] = (df_data['cantidad'].astype(float) / float(total_matriculados) * 100) if total_matriculados > 0 else 0
    df_display = df_data.copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
    df_display = df_display[['#', 'grado', 'cantidad', 'porcentaje']]
    df_display.columns = ['#', 'Grado', 'Matriculados', 'Porcentaje']
    st.dataframe(df_display, use_container_width=True, hide_index=True)

@st.cache_data
def load_data_by_stage(_engine, year, stage):
    table_name = "Grados_2021_2025"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(), 0
        
        params = {'year': year, 'stage': stage}
        query_data = text(f"""
            SELECT 
                GRADO as grado, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE FECHA = :year
              AND ETAPA = :stage
              AND GRADO IS NOT NULL 
              AND GRADO != '' 
            GROUP BY grado
            ORDER BY cantidad DESC
        """)
        df = pd.DataFrame(connection.execute(query_data, params).fetchall(), columns=["grado", "cantidad"])
        
        query_total = text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE FECHA = :year AND ETAPA = :stage")
        total_matriculados = connection.execute(query_total, params).scalar() or 0
        
        return df, total_matriculados

try:
    available_years = get_available_years(engine)
    if not available_years:
        st.warning(f"⚠️ No se encontraron datos en la tabla Grados_2021_2025.")
        st.stop()

    if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
        st.session_state.selected_year = available_years[0]
    selected_year = st.session_state.selected_year

    # Cargar datos para ambas etapas
    df_etapa1, total_etapa1 = load_data_by_stage(engine, selected_year, 1)
    df_etapa2, total_etapa2 = load_data_by_stage(engine, selected_year, 2)

    # --- Barra Lateral ---
    st.sidebar.info(f"**Año:** {selected_year}")
    st.sidebar.divider()
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Matriculados Etapa 1 ({selected_year})", f"{int(total_etapa1):,}")
    st.sidebar.metric(f"Matriculados Etapa 2 ({selected_year})", f"{int(total_etapa2):,}")
    st.sidebar.divider()
    if os.path.exists("assets/Logo_rionegro.png"):
        st.sidebar.image("assets/Logo_rionegro.png")

    # --- Selección de Año con Botones ---
    st.write("📅 **Seleccionar Año para Visualizar**")
    cols_buttons = st.columns(len(available_years))
    def set_year(year):
        st.session_state.selected_year = year

    for i, year in enumerate(available_years):
        with cols_buttons[i]:
            button_type = "primary" if year == selected_year else "secondary"
            st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))
    st.markdown('<hr class="compact">', unsafe_allow_html=True)

    # --- Layout de Gráficos ---
    col1, col2 = st.columns(2)

    with col1:
        create_donut_chart_and_table(df_etapa1, total_etapa1, f"📊 Etapa 1 - Año {selected_year}")

    with col2:
        create_donut_chart_and_table(df_etapa2, total_etapa2, f"📊 Etapa 2 - Año {selected_year}")

except Exception as e:
    st.error("❌ Error al cargar o procesar los datos")
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