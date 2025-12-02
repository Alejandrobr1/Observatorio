import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import create_engine, text
import sys 
import os
from dashboard_config import create_nav_buttons, get_current_page_category
# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes Comfenalco por Población")
st.title("📊 Estudiantes Matriculados por Población (Comfenalco)")

# --- Set Category State ---
current_page_category = get_current_page_category(os.path.basename(__file__))
if 'population_filter' not in st.session_state or st.session_state.population_filter != current_page_category:
    st.session_state.population_filter = current_page_category

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
    # En producción (Streamlit Cloud), lee desde st.secrets
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

# --- Lógica de Estado y Filtros ---

@st.cache_data
def get_available_years(_engine, prefix):
    table_name = "Estudiantes_2016_2019" # Tabla consolidada
    if prefix == "Estudiantes":
        with _engine.connect() as connection:
            if _engine.dialect.has_table(connection, table_name):
                query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} ORDER BY FECHA DESC")
                years = [row[0] for row in connection.execute(query_years).fetchall()]
                if years:
                    return years
                st.warning(f"La tabla '{table_name}' no contiene años en la columna 'FECHA'. Usando año por defecto.")
                return [pd.Timestamp.now().year] # Devuelve el año actual si no hay datos
    else: # Para Docentes
        with _engine.connect() as connection:
            query_tables = text(f"SHOW TABLES LIKE '{prefix}_%'")
            years = [row[0].split('_')[1] for row in connection.execute(query_tables).fetchall() if len(row[0].split('_')) > 1 and row[0].split('_')[1].isdigit()]
            if years:
                return sorted(years, reverse=True)
    return []

st.sidebar.header("Filtros")
selected_pop = st.session_state.population_filter

population_prefix = "Estudiantes"
available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning(f"⚠️ No se encontraron datos para '{selected_pop}'.")
    st.stop()

# FORZAR REINICIO DEL AÑO: Si el año guardado en la sesión no es válido para
# los datos de ESTA PÁGINA, se reinicia al año más reciente disponible.
if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.info(f"**Población:** {selected_pop}")
st.sidebar.info(f"**Año:** {selected_year}")
st.sidebar.divider()

# --- Carga de Datos ---
@st.cache_data
def load_data_by_stage(_engine, prefix, year, stage):
    # Si son estudiantes, usar la tabla consolidada. Si no, mantener la lógica anterior.
    table_name = "Estudiantes_2016_2019" if prefix == "Estudiantes" else f"{prefix}_{year}"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(columns=["POBLACION", "cantidad"]), 0, 0
        params = {'year': year, 'stage': stage}
        query = text(f"""
            SELECT 
                POBLACION, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE POBLACION IS NOT NULL AND POBLACION != '' AND POBLACION != 'SIN INFORMACION'
              AND ETAPA = :stage
              AND FECHA = :year
            GROUP BY POBLACION
            ORDER BY cantidad DESC
        """)
        result = connection.execute(query, params)
        df = pd.DataFrame(result.fetchall(), columns=["POBLACION", "cantidad"])

        # Métricas
        total_matriculados = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE ETAPA = :stage AND FECHA = :year"), params).scalar() or 0
        total_poblacion = connection.execute(text(f"SELECT COUNT(DISTINCT POBLACION) FROM {table_name} WHERE ETAPA = :stage AND FECHA = :year AND POBLACION IS NOT NULL AND POBLACION != ''"), params).scalar() or 0

        return df, total_matriculados, total_poblacion

def create_population_chart(df, total_matriculados, title):
    """Función para crear un gráfico de barras y una tabla para una etapa específica."""
    st.header(title)
    if df.empty:
        st.warning(f"No hay datos de matriculados por población para esta etapa.")
        return

    # Gráfico de barras verticales
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df)))
    bars = ax.bar(df['POBLACION'], df['cantidad'], color=colors, edgecolor='black', linewidth=1.2)

    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height):,}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Tipo de Población', fontsize=13, fontweight='bold')
    ax.set_ylabel('Cantidad de Estudiantes Matriculados', fontsize=13, fontweight='bold')
    ax.set_title(f'Estudiantes por Población', fontsize=16, fontweight='bold', pad=20)
    plt.xticks(rotation=45, ha="right")

    max_val = df['cantidad'].max() if not df.empty else 1
    ax.set_ylim(0, float(max_val) * 1.2)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig)

    # Tabla de datos detallada
    df['porcentaje'] = (pd.to_numeric(df['cantidad']) / float(total_matriculados) * 100) if total_matriculados > 0 else 0
    df_display = df.copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.1f}%")
    df_display = df_display[['#', 'POBLACION', 'cantidad', 'porcentaje']]
    df_display.columns = ['#', 'Población', 'Matriculados', 'Porcentaje']
    st.header("📋 Tabla Detallada")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

try:
    df_etapa1, total_matriculados_etapa1, total_poblacion_etapa1 = load_data_by_stage(engine, population_prefix, selected_year, '1')
    df_etapa2, total_matriculados_etapa2, total_poblacion_etapa2 = load_data_by_stage(engine, population_prefix, selected_year, '2')

    # --- Visualización ---
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Matriculados Etapa 1 ({selected_year})", f"{int(total_matriculados_etapa1):,}")
    st.sidebar.metric(f"Matriculados Etapa 2 ({selected_year})", f"{int(total_matriculados_etapa2):,}")
    st.sidebar.divider()
    # Añadir el logo al final del sidebar
    if os.path.exists("assets/Logo_rionegro.png"):
        st.sidebar.image("assets/Logo_rionegro.png")

    # --- Selección de Año con Botones Horizontales ---
    st.write("📅 **Seleccionar Año para Visualizar**")
    cols_buttons = st.columns(len(available_years))
    def set_year(year):
        st.session_state.selected_year = year

    for i, year in enumerate(available_years):
        with cols_buttons[i]:
            button_type = "primary" if year == selected_year else "secondary"
            st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))
    st.divider()

    # Layout en dos columnas para los gráficos
    col1, col2 = st.columns(2)

    with col1:
        create_population_chart(df_etapa1, total_matriculados_etapa1, f"📊 Etapa 1 - Año {selected_year}")

    with col2:
        create_population_chart(df_etapa2, total_matriculados_etapa2, f"📊 Etapa 2 - Año {selected_year}")

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())

def add_interest_links():
    st.markdown("---")
    st.markdown("### 🔗 Oportunidades laborales")
    st.markdown("""
    - [Agencia pública de empleo – Comfenalco Antioquia](https://www.comfenalcoantioquia.com.co/personas/sedes/oficina-de-empleo-oriente)
    - [Agencia Pública de Empleo Municipio de Rionegro](https://www.comfenalcoantioquia.com.co/personas/servicios/agencia-de-empleo/ofertas)
    - [Agencia Pública de Empleo SENA](https://ape.sena.edu.co/Paginas/Inicio.aspx) 
    """)
add_interest_links()