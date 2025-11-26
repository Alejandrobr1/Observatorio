import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import create_engine, text
import sys
import os

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Etapa")
st.title("📊 Comparativa de Estudiantes por Etapa y Sede (Comfenalco)")

# --- State and Navigation ---
if 'population_filter' not in st.session_state:
    st.session_state.population_filter = "Estudiantes Comfenalco"

def create_nav_buttons(selected_pop):
    nav_cols = st.columns(8)
    with nav_cols[0]:
        st.page_link("app.py", label="Inicio", icon="🏠")

    if selected_pop == "Estudiantes Comfenalco":
        links = {
            "Sede Nodal": "pages/1p-estudiantes_matriculados_por_sede_nodal.py",
            "Jornada/Día": "pages/2p-estudiantes_por_jornada_dia.py",
            "Población": "pages/3p-estudiantes_por_poblacion.py",
            "Participación %": "pages/4p-estudiantes_matriculados_sede_porcentaje.py",
            "Etapas (Pastel)": "pages/5p-estudiantes_por_sede_nodal_etapa1_2.py",
            "Etapas (Barras)": "pages/6p-estudiantes_por_sede_nodal_barras_etp1_2.py",
            "Escuela Nueva (Sede)": "pages/7p-estudiantes_escuela_nueva.py",
            "Escuela Nueva (IE)": "pages/8p-estudiantes_por_institucion.py"
        }
        # Re-ajustar columnas para acomodar todos los botones
        nav_cols = st.columns(len(links) + 1)
        with nav_cols[0]:
            st.page_link("app.py", label="Inicio", icon="🏠")
        for i, (label, page) in enumerate(links.items()):
            with nav_cols[i+1]:
                st.page_link(page, label=label)

    elif selected_pop == "Docentes":
        with nav_cols[1]:
            st.page_link("pages/9p-docentes_por_nivel.py", label="Docentes por Nivel", icon="🎓")
        with nav_cols[2]:
            st.page_link("pages/10p-docentes_por_institucion.py", label="Docentes por Institución", icon="🏫")

    elif selected_pop == "Estudiantes Colombo":
        with nav_cols[1]:
            st.page_link("pages/11p-colombo_por_institucion.py", label="Colombo por Institución", icon="🏫")
        with nav_cols[2]:
            st.page_link("pages/12p-colombo_por_nivel.py", label="Colombo por Nivel", icon="📈")

create_nav_buttons(st.session_state.population_filter)
st.markdown("---")
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
            else:
                st.warning(f"La tabla '{table_name}' no existe. Usando año por defecto.")
                return [pd.Timestamp.now().year]
            st.warning(f"La tabla '{table_name}' no contiene años en la columna 'FECHA'. Usando año por defecto.")
            return [pd.Timestamp.now().year]
    else: # Para Docentes
        with _engine.connect() as connection:
            query_tables = text(f"SHOW TABLES LIKE '{prefix}_%'")
            years = [row[0].split('_')[1] for row in connection.execute(query_tables).fetchall() if len(row[0].split('_')) > 1 and row[0].split('_')[1].isdigit()]
            if years:
                return sorted(years, reverse=True)
    return []

st.sidebar.header("Filtros")
selected_population = st.sidebar.selectbox(
    "Filtrar por tipo de población",
    ["Estudiantes Comfenalco", "Estudiantes Colombo", "Docentes"],
    index=["Estudiantes Comfenalco", "Estudiantes Colombo", "Docentes"].index(st.session_state.population_filter),
    key="population_filter",
    help="Selecciona el grupo de datos a visualizar."
)
st.sidebar.divider()

if selected_population != "Estudiantes Comfenalco":
    st.info(f"Este dashboard es para 'Estudiantes Comfenalco'. Por favor, selecciona esa opción en el filtro de población para ver los datos.")
    st.stop()

population_prefix = "Estudiantes"
available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning(f"⚠️ No se encontraron datos para '{selected_population}'.")
    st.stop()

# FORZAR REINICIO DEL AÑO: Si el año guardado en la sesión no es válido para
# los datos de ESTA PÁGINA, se reinicia al año más reciente disponible.
if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.info(f"**Población:** {selected_population}")
st.sidebar.info(f"**Año:** {selected_year}")
st.sidebar.divider()

# Función para generar gráfico de barras y tabla
def create_bar_chart_and_table(df_data, total_etapa, title):
    st.header(title)
    
    if df_data.empty:
        st.warning("No hay datos para esta etapa.")
        return

    df_data['cantidad'] = pd.to_numeric(df_data['cantidad'])

    # Crear el gráfico de barras verticales
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_data)))
    bars = ax.bar(df_data['SEDE_NODAL'], df_data['cantidad'], color=colors, edgecolor='black', linewidth=1.2)

    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height):,}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Sede Nodal', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cantidad de Matriculados', fontsize=12, fontweight='bold')
    ax.set_title('Matriculados por Sede Nodal', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(rotation=45, ha="right")
    max_val = df_data['cantidad'].max() if not df_data.empty else 1
    ax.set_ylim(0, float(max_val) * 1.2)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("📋 Resumen")
    df_data['porcentaje'] = (df_data['cantidad'] / float(total_etapa) * 100) if total_etapa > 0 else 0
    df_display = df_data.copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.1f}%")
    df_display = df_display[['#', 'SEDE_NODAL', 'cantidad', 'porcentaje']]
    df_display.columns = ['#', 'Sede Nodal', 'Matriculados', 'Porcentaje']
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- Carga de Datos ---
@st.cache_data
def load_data_by_stage(_engine, year, prefix, stage):
    # Si son estudiantes, usar la tabla consolidada. Si no, mantener la lógica anterior.
    table_name = "Estudiantes_2016_2019" if prefix == "Estudiantes" else f"{prefix}_{year}"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(columns=["SEDE_NODAL", "cantidad"]), 0
        params = {'year': year, 'stage': stage}
        query = text(f"""
            SELECT 
                SEDE_NODAL, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE ETAPA = :stage
              AND SEDE_NODAL IS NOT NULL AND SEDE_NODAL != '' AND SEDE_NODAL != 'SIN INFORMACION'
              AND FECHA = :year
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        result = connection.execute(query, params)
        df = pd.DataFrame(result.fetchall(), columns=["SEDE_NODAL", "cantidad"])
        total_matriculados_stage = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE ETAPA = :stage AND FECHA = :year"), params).scalar() or 0
        return df, total_matriculados_stage

try:
    df_etapa1, total_etapa1 = load_data_by_stage(engine, selected_year, population_prefix, '1')
    df_etapa2, total_etapa2 = load_data_by_stage(engine, selected_year, population_prefix, '2')
    total_matriculados = total_etapa1 + total_etapa2

    # --- Visualización ---
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
    st.sidebar.metric(f"Matriculados Etapa 1 ({selected_year})", f"{int(total_etapa1):,}")
    st.sidebar.metric(f"Matriculados Etapa 2 ({selected_year})", f"{int(total_etapa2):,}")
    st.sidebar.divider()

    col1, col2 = st.columns(2)
    with col1:
        create_bar_chart_and_table(df_etapa1, total_etapa1, f"📊 Etapa 1 - Año {selected_year}")
    with col2:
        create_bar_chart_and_table(df_etapa2, total_etapa2, f"📊 Etapa 2 - Año {selected_year}")

    # --- Selección de Año con Botones ---
    st.divider()
    with st.expander("📅 **Seleccionar Año para Visualizar**", expanded=True):
        st.write("Haz clic en un botón para cambiar el año de los datos mostrados en los gráficos.")
        
        cols_buttons = st.columns(len(available_years))
        
        def set_year(year):
            st.session_state.selected_year = year

        for i, year in enumerate(available_years):
            with cols_buttons[i]:
                button_type = "primary" if year == selected_year else "secondary"
                st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)