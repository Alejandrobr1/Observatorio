import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import create_engine, text
import sys 
import os
from dashboard_config import create_nav_buttons, get_current_page_category
from dashboard_config import COMFENALCO_LABEL
# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes Comfenalco por Jornada y Día")
st.title("📊 Estudiantes por Jornada y día (Comfenalco)")

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
            years = []
            for row in connection.execute(query_tables).fetchall():
                parts = row[0].split('_')
                if len(parts) > 1 and parts[1].isdigit():
                    years.append(parts[1])
            if years:
                return sorted(years, reverse=True)
    return []

population_prefix = "Estudiantes"
available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning(f"⚠️ No se encontraron datos para '{st.session_state.population_filter}'.")
    st.stop()

# FORZAR REINICIO DEL AÑO: Si el año guardado en la sesión no es válido para
# los datos de ESTA P.PY, se reinicia al año más reciente disponible.
if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.info(f"**Población:** {st.session_state.population_filter}")
st.sidebar.info(f"**Año:** {selected_year}")
st.sidebar.divider()

# --- Carga de Datos ---
@st.cache_data
def load_data_by_stage(_engine, prefix, year, stage):
    # Si son estudiantes, usar la tabla consolidada. Si no, mantener la lógica anterior.
    table_name = "Estudiantes_2016_2019" if prefix == "Estudiantes" else f"{prefix}_{year}"
    
    # Verificar si la tabla existe antes de consultarla
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(columns=["DIA", "JORNADA", "cantidad"]), 0, 0, 0

    with _engine.connect() as connection:
        params = {'year': year, 'stage': stage}
        query = text(f"""
            SELECT 
                DIA, JORNADA, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE DIA IS NOT NULL AND DIA != '' AND DIA != 'SIN INFORMACION'
              AND JORNADA IS NOT NULL AND JORNADA != '' AND JORNADA != 'SIN INFORMACION'
              AND ETAPA = :stage
              AND FECHA = :year
            GROUP BY DIA, JORNADA
            ORDER BY DIA, JORNADA
        """)
        result = connection.execute(query, params)
        df = pd.DataFrame(result.fetchall(), columns=["DIA", "JORNADA", "cantidad"])
        
        # Métricas
        total_matriculados = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE ETAPA = :stage AND FECHA = :year"), params).scalar() or 0
        total_jornadas = connection.execute(text(f"SELECT COUNT(DISTINCT JORNADA) FROM {table_name} WHERE ETAPA = :stage AND FECHA = :year AND JORNADA IS NOT NULL AND JORNADA != ''"), params).scalar() or 0
        total_dias = connection.execute(text(f"SELECT COUNT(DISTINCT DIA) FROM {table_name} WHERE ETAPA = :stage AND FECHA = :year AND DIA IS NOT NULL AND DIA != ''"), params).scalar() or 0
        
        return df, total_matriculados, total_jornadas, total_dias

def create_day_journey_chart(df, title):
    """Función para crear un gráfico de barras agrupadas para una etapa específica."""
    st.header(title)
    if df.empty:
        st.warning("No hay datos de Estudiantes por Jornada y día para esta etapa.")
        return

    # Pivotear los datos para tener días como índice y jornadas como columnas
    df_pivot = df.pivot(index='DIA', columns='JORNADA', values='cantidad').fillna(0)

    # Crear gráfico de barras verticales agrupadas
    fig, ax = plt.subplots(figsize=(14, 8))
    dias = df_pivot.index
    jornadas = df_pivot.columns
    n_dias = len(dias)
    n_jornadas = len(jornadas)
    x = np.arange(n_dias)  # Posiciones de los grupos de barras (días)
    width = 0.8 / n_jornadas  # Ancho de cada barra
    colors = plt.cm.viridis(np.linspace(0, 1, n_jornadas))
    
    for i, jornada in enumerate(jornadas):
        offset = width * (i - (n_jornadas - 1) / 2)
        valores = df_pivot[jornada]
        bars = ax.bar(x + offset, valores, width, label=jornada, color=colors[i], edgecolor='black', linewidth=1)
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height):,}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Día de la Semana', fontsize=13, fontweight='bold')
    ax.set_ylabel('Cantidad de Estudiantes Matriculados', fontsize=13, fontweight='bold')
    ax.set_title('Estudiantes por Jornada y día', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(dias, rotation=45, ha='right', fontsize=11)
    ax.legend(title='Jornada', fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    max_val = df_pivot.sum(axis=1).max() if not df_pivot.empty else 1
    ax.set_ylim(0, float(max_val) * 1.2)
    plt.tight_layout()
    st.pyplot(fig)

    # Tabla de datos detallada
    df_display = df_pivot.copy()
    df_display = df_display.astype(int).applymap('{:,}'.format)
    df_display['Total por Día'] = df_pivot.sum(axis=1).astype(int).apply('{:,}'.format)
    st.header("📋 Tabla Detallada")
    st.dataframe(df_display, use_container_width=True)

try:
    df_etapa1, total_matriculados_etapa1, _, _ = load_data_by_stage(engine, population_prefix, selected_year, '1')
    df_etapa2, total_matriculados_etapa2, _, _ = load_data_by_stage(engine, population_prefix, selected_year, '2')

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
            st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,)) # type: ignore
    st.markdown('<hr class="compact">', unsafe_allow_html=True)

    # Layout en dos columnas para los gráficos
    col1, col2 = st.columns(2)

    with col1:
        create_day_journey_chart(df_etapa1, f"📊 Etapa 1 - Año {selected_year}")

    with col2:
        create_day_journey_chart(df_etapa2, f"📊 Etapa 2 - Año {selected_year}")

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
