import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import create_engine, text
import sys
import os
from dashboard_config import create_nav_buttons
from dashboard_config import COMFENALCO_LABEL


# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Configurar streamlit
st.set_page_config(layout="wide", page_title="Horas de Formación por Sede (Francés)")
st.title("📊 Horas de Formación por Sede Nodal (Francés Intensificación)")


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


@st.cache_data
def get_available_years(_engine):
    table_name = "Frances_intensificacion_horas"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            st.warning(f"La tabla '{table_name}' no existe.")
            return []
        query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} WHERE FECHA IS NOT NULL ORDER BY FECHA DESC")
        years = [row[0] for row in connection.execute(query_years).fetchall()]
        if years:
            return years
    st.warning(f"No se encontraron años en la tabla '{table_name}'.")
    return []

@st.cache_data
def get_available_sedes(_engine, year):
    """Obtiene las sedes nodales disponibles para un año específico."""
    table_name = "Frances_intensificacion_horas"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return []
        query_sedes = text(f"""
            SELECT DISTINCT SEDE_NODAL FROM {table_name} 
            WHERE FECHA = :year AND SEDE_NODAL IS NOT NULL AND SEDE_NODAL != ''
            ORDER BY SEDE_NODAL ASC
        """)
        return [row[0] for row in connection.execute(query_sedes, {'year': year}).fetchall()]


def create_bar_chart_and_table(df_data, total_horas, title, sede_nodal):
    st.header(f"📊 {title} - Año {st.session_state.selected_year} - Sede: {sede_nodal}")
    
    if df_data.empty:
        st.warning("No hay datos de horas de formación para el año seleccionado.")
        return

    # Asegurar que total_horas sea numérico
    df_data['total_horas'] = pd.to_numeric(df_data['total_horas'], errors='coerce')
    df_data = df_data.dropna(subset=['total_horas'])
    df_data = df_data[df_data['total_horas'] > 0]
    
    if df_data.empty:
        st.warning("No hay datos válidos de horas de formación para el año seleccionado.")
        return

    # Gráfico de barras verticales
    st.subheader("Visualización por Sede Nodal")
    df_sorted = df_data.sort_values('total_horas', ascending=True).copy()
    
    # Convertir explícitamente a array de numpy con tipo float
    horas_values = df_sorted['total_horas'].values.astype(float)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    y_pos = np.arange(len(df_sorted))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_sorted)))
    
    bars = ax.barh(y_pos, horas_values, color=colors, edgecolor='black', linewidth=1.2)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted['sede'].values)
    ax.set_xlabel('Total de Horas de Formación')
    ax.set_ylabel('Sede')
    ax.set_title(f'Horas de Formación por Sede - Sede Nodal: {sede_nodal}')
    
    # Añadir valores sobre las barras
    for i, (bar, value) in enumerate(zip(bars, horas_values)):
        width = bar.get_width()
        # Posicionar el texto ligeramente a la derecha de la barra
        ax.text(width + (ax.get_xlim()[1] * 0.01), bar.get_y() + bar.get_height() / 2,
                f'{int(value):,}', ha='left', va='center', fontsize=9)
    
    # Configurar el eje X para empezar desde 0 y ajustar el límite
    ax.set_xlim(left=0, right=ax.get_xlim()[1] * 1.15) # Añadir un 15% de espacio para las etiquetas
    
    ax.grid(axis='x', linestyle='--', alpha=0.6) # Rejilla en el eje de valores (X)
    plt.tight_layout()
    st.pyplot(fig)


    # Tabla de resumen
    st.subheader("📋 Resumen por Sede Nodal")
    df_data['porcentaje'] = (df_data['total_horas'].astype(float) / float(total_horas) * 100) if total_horas > 0 else 0
    df_display = df_data.sort_values('total_horas', ascending=False).copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['total_horas'] = df_display['total_horas'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
    df_display = df_display[['#', 'sede', 'total_horas', 'porcentaje']]
    df_display.columns = ['#', 'Sede', 'Total Horas', 'Porcentaje']
    st.dataframe(df_display, width='stretch', hide_index=True)


@st.cache_data
def load_data(_engine, year, sede_nodal):
    table_name = "Frances_intensificacion_horas"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(), 0
        
        params = {'year': year, 'sede_nodal': sede_nodal} # Corregido para usar sede_nodal
        query_data = text(f"""
            SELECT 
                SEDE,
                COALESCE(SUM(HORAS), 0) as total_horas
            FROM {table_name}
            WHERE FECHA = :year
              AND SEDE_NODAL = :sede_nodal
              AND SEDE IS NOT NULL AND SEDE != ''
            GROUP BY SEDE, SEDE_NODAL
            ORDER BY total_horas DESC
        """)
        
        result = connection.execute(query_data, params).fetchall()
        df = pd.DataFrame(result, columns=["sede", "total_horas"])
        
        if df.empty:
            return pd.DataFrame(), 0
        
        # Calcular total
        total_horas_query = text(f"""
            SELECT SUM(HORAS) FROM {table_name} 
            WHERE FECHA = :year AND SEDE_NODAL = :sede_nodal
        """)
        total_horas = connection.execute(total_horas_query, params).scalar() or 0
        
        return df, total_horas


try:
    available_years = get_available_years(engine)
    if not available_years:
        st.warning("⚠️ No se encontraron datos en la tabla 'Frances_intensificacion_horas'.")
        st.stop()


    if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
        st.session_state.selected_year = available_years[0]
    selected_year = st.session_state.selected_year

    available_sedes = get_available_sedes(engine, selected_year)
    if not available_sedes:
        st.warning(f"⚠️ No se encontraron sedes para el año {selected_year}.")
        st.stop()

    if 'selected_sede' not in st.session_state or st.session_state.selected_sede not in available_sedes:
        st.session_state.selected_sede = available_sedes[0]

    selected_sede = st.sidebar.selectbox("📍 Seleccionar Sede Nodal", available_sedes, index=available_sedes.index(st.session_state.selected_sede))
    st.session_state.selected_sede = selected_sede

    df_data, total_horas = load_data(engine, selected_year, selected_sede)


    # --- Barra Lateral ---
    st.sidebar.info(f"**Año:** {selected_year}")
    st.sidebar.divider()
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Horas ({selected_sede}, {selected_year})", f"{int(total_horas):,}")
    st.sidebar.divider()
    if os.path.exists("assets/Logo_rionegro.png"):
        st.sidebar.image("assets/Logo_rionegro.png")


    # --- Layout Principal ---
    col1, col2 = st.columns([3, 1])


    with col1:
        create_bar_chart_and_table(df_data, total_horas, "Horas de Formación por Sede", selected_sede)


    with col2:
        st.write("📅 **Seleccionar Año**")
        def set_year(year):
            st.session_state.selected_year = year
        for year in available_years:
            button_type = "primary" if year == selected_year else "secondary"
            st.button(str(year), key=f"year_{year}", width='stretch', type=button_type, on_click=set_year, args=(year,))


except Exception as e:
    st.error("❌ Error al cargar o procesar los datos")
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
