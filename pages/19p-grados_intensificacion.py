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
st.set_page_config(layout="wide", page_title="Matriculados por Grado y Sede (Intensificación)")
st.title("📊 Matriculados por Grado y Sede Nodal (Intensificación)")

# --- State and Navigation ---
if 'population_filter' not in st.session_state:
    st.session_state.population_filter = COMFENALCO_LABEL

create_nav_buttons(st.session_state.population_filter)
st.markdown('<hr class="compact">', unsafe_allow_html=True)
st.markdown("""
<style>
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
    db_user = st.secrets["DB_USER"]
    db_pass = st.secrets["DB_PASS"]
    db_host = st.secrets["DB_HOST"]
    db_port = st.secrets["DB_PORT"]
    db_name = st.secrets["DB_NAME"]
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string, pool_pre_ping=True)

try:
    engine = get_engine()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

@st.cache_data
def get_available_years(_engine):
    table_name = "Grados_intensificacion"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return []
        query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} ORDER BY FECHA DESC")
        return [row[0] for row in connection.execute(query_years).fetchall()]

@st.cache_data
def get_available_sedes(_engine, year):
    table_name = "Grados_intensificacion"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return []
        query_sedes = text(f"SELECT DISTINCT SEDE_NODAL FROM {table_name} WHERE FECHA = :year AND SEDE_NODAL IS NOT NULL AND SEDE_NODAL != '' ORDER BY SEDE_NODAL ASC")
        return [row[0] for row in connection.execute(query_sedes, {'year': year}).fetchall()]

def create_grouped_bar_chart_and_table(df_data, title):
    st.header(title)

    if df_data.empty:
        st.warning("No hay datos de matriculados para el año seleccionado.")
        return

    # Pivotear los datos para tener grados como índice y sedes como columnas
    df_pivot = df_data.pivot(index='grado', columns='sede_nodal', values='cantidad').fillna(0)

    # Crear gráfico de barras verticales agrupadas
    st.subheader("Comparativa de Matriculados por Grado y Sede Nodal")
    fig, ax = plt.subplots(figsize=(14, 8))
    grados = df_pivot.index
    sedes = df_pivot.columns
    n_grados = len(grados)
    n_sedes = len(sedes)
    x = np.arange(n_grados)  # Posiciones de los grupos de barras (grados)
    width = 0.8 / n_sedes  # Ancho de cada barra
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, n_sedes))
    
    for i, sede in enumerate(sedes):
        offset = width * (i - (n_sedes - 1) / 2)
        valores = df_pivot[sede]
        bars = ax.bar(x + offset, valores, width, label=sede, color=colors[i], edgecolor='black', linewidth=1)
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height):,}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, rotation=90)
    
    ax.set_xlabel('Grado', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cantidad de Matriculados', fontsize=12, fontweight='bold')
    ax.set_title('Matriculados por Sede Nodal en cada Grado', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(grados, rotation=45, ha='right')
    ax.legend(title='Sede Nodal', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    max_val = df_pivot.sum(axis=1).max() if not df_pivot.empty else 1
    ax.set_ylim(0, float(max_val) * 1.2)
    plt.tight_layout()
    st.pyplot(fig)

    # Tabla de datos detallada
    st.subheader("📋 Tabla de Datos")
    df_display = df_pivot.copy().astype(int)
    st.dataframe(df_display.T, use_container_width=True) # Transponemos para que coincida con el gráfico original

@st.cache_data
def load_all_data(_engine, year):
    table_name = "Grados_intensificacion"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(), 0
        
        params = {'year': year}
        query_data = text(f"""
            SELECT 
                SEDE_NODAL as sede_nodal, GRADO as grado, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE FECHA = :year
              AND SEDE_NODAL IS NOT NULL AND SEDE_NODAL != ''
              AND GRADO IS NOT NULL AND GRADO != '' 
            GROUP BY sede_nodal, grado
            ORDER BY sede_nodal, grado ASC
        """)
        df = pd.DataFrame(connection.execute(query_data, params).fetchall(), columns=["sede_nodal", "grado", "cantidad"])
        
        query_total = text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE FECHA = :year")
        total_matriculados = connection.execute(query_total, params).scalar() or 0
        
        return df, total_matriculados

try:
    available_years = get_available_years(engine)
    if not available_years:
        st.warning(f"⚠️ No se encontraron datos en la tabla Grados_intensificacion.")
        st.stop()

    if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
        st.session_state.selected_year = available_years[0]
    selected_year = st.session_state.selected_year

    # Cargar todos los datos para el año seleccionado
    df_data, total_matriculados = load_all_data(engine, selected_year)

    # --- Barra Lateral ---
    st.sidebar.info(f"**Año:** {selected_year}")
    st.sidebar.divider()
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
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
    create_grouped_bar_chart_and_table(df_data, f"Año {selected_year}")

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