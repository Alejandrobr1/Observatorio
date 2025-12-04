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
st.set_page_config(layout="wide", page_title="Nivel MCER por Grado (Francés)")
st.title("📊 Nivel MCER por Grado (Francés Intensificación)")


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


available_years = get_available_years(engine)


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
def load_data(_engine, year):
    table_name = "Frances_intensificacion_horas"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(columns=["GRADO", "NIVEL_MCER", "cantidad"]), 0
        
        params = {'year': year}
        
        # Query simple sin filtros complejos - dejar que pandas filtre
        query = text(f"""
            SELECT 
                GRADO, NIVEL_MCER, MATRICULADOS
            FROM {table_name}
            WHERE FECHA = :year
        """)
        
        result = connection.execute(query, params)
        df = pd.DataFrame(result.fetchall(), columns=["GRADO", "NIVEL_MCER", "MATRICULADOS"])
        
        if df.empty:
            return pd.DataFrame(columns=["GRADO", "NIVEL_MCER", "cantidad"]), 0
        
        # Limpiar y filtrar con pandas
        df['GRADO'] = df['GRADO'].astype(str).str.strip()
        df['NIVEL_MCER'] = df['NIVEL_MCER'].astype(str).str.strip()
        df['MATRICULADOS'] = pd.to_numeric(df['MATRICULADOS'], errors='coerce').fillna(0)

        # Filtrar valores no válidos
        df = df[
            (df['GRADO'].notna()) & 
            (df['GRADO'] != '') & 
            (df['GRADO'] != 'None') &
            (df['GRADO'].str.upper() != 'SIN INFORMACION') &
            (df['GRADO'].str.upper() != 'SIN INFORMACIÓN') &            
            (df['NIVEL_MCER'].notna()) & 
            (df['NIVEL_MCER'] != '') & 
            (df['NIVEL_MCER'] != 'None') &
            (df['NIVEL_MCER'].str.upper() != 'SIN INFORMACION') &
            (df['NIVEL_MCER'].str.upper() != 'SIN INFORMACIÓN')
        ]
        
        # Agrupar y contar
        df_grouped = df.groupby(['GRADO', 'NIVEL_MCER'])['MATRICULADOS'].sum().reset_index(name='cantidad')
        
        # Contar total de matriculados
        # Se recalcula la suma desde el dataframe ya filtrado y limpio para consistencia
        total_matriculados = df['MATRICULADOS'].sum()
        
        return df_grouped, total_matriculados


def create_data_table(df):
    """Función para crear y mostrar una tabla detallada de los datos."""
    st.header("📋 Tabla Detallada")
    if df.empty:
        st.warning("No hay datos para mostrar en la tabla.")
        return

    df_pivot = df.pivot(index='GRADO', columns='NIVEL_MCER', values='cantidad').fillna(0).astype(int)
    df_pivot['Total por Grado'] = df_pivot.sum(axis=1)
    
    # Añadir fila de totales
    total_row = df_pivot.sum().rename('Total General').to_frame().T
    df_display = pd.concat([df_pivot, total_row])

    st.dataframe(df_display, width='stretch')


def create_stacked_bar_chart(df, title):
    """Función para crear un gráfico de barras apiladas de Nivel MCER por Grado."""

    # Pivotear los datos para tener grados como índice y niveles como columnas
    df_pivot = df.pivot(index='GRADO', columns='NIVEL_MCER', values='cantidad').fillna(0)

    # Crear gráfico de barras verticales apiladas
    fig, ax = plt.subplots(figsize=(14, 8))
    grados = df_pivot.index
    niveles = df_pivot.columns
    n_grados = len(grados)
    n_niveles = len(niveles)
    x = np.arange(n_grados)
    width = 0.7  # Ancho de las barras
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, n_niveles))
    
    bottom = np.zeros(n_grados)

    for i, nivel in enumerate(niveles):
        valores = df_pivot[nivel]
        bars = ax.bar(x, valores, width, label=nivel, color=colors[i], bottom=bottom, edgecolor='black', linewidth=0.5)
        
        # Añadir etiquetas en el centro de cada segmento
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                y_pos = bar.get_y() + height / 2
                ax.annotate(f'{int(height):,}',
                            xy=(bar.get_x() + bar.get_width() / 2, y_pos),
                            ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        
        bottom += valores.values

    ax.set_xlabel('Grado', fontsize=13, fontweight='bold')
    ax.set_ylabel('Cantidad de Estudiantes Matriculados', fontsize=13, fontweight='bold')
    ax.set_title('Composición de Estudiantes por Nivel MCER en cada Grado', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(grados, rotation=45, ha='right', fontsize=11)
    ax.legend(title='Nivel MCER', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    max_val = df_pivot.sum(axis=1).max() if not df_pivot.empty else 1
    ax.set_ylim(0, float(max_val) * 1.2)
    plt.tight_layout()
    st.pyplot(fig)

try:
    df_data, total_matriculados = load_data(engine, selected_year)


    # --- Visualización ---
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
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
            st.button(str(year), key=f"year_{year}", on_click=set_year, args=(year,), type=button_type, width='stretch')


    st.markdown('<hr class="compact">', unsafe_allow_html=True)
    
    if df_data.empty:
        st.warning(f"No hay datos de niveles MCER por grado para el año {selected_year}.")
    else:
        # Mostrar la tabla de datos primero
        create_data_table(df_data)

        # Mostrar el gráfico
        st.header(f"📊 Gráfico: Año {selected_year}")
        create_stacked_bar_chart(df_data, f"Año {selected_year}")


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
