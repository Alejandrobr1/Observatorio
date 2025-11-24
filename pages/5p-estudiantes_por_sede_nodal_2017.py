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
st.set_page_config(layout="wide", page_title="Dashboard Participación por Etapa y Sede Nodal")
st.title("📊 Participación por Etapa y Sede Nodal")

@st.cache_resource
def get_engine():
    # En producción (Streamlit Cloud), lee desde st.secrets
    db_user = st.secrets["DB_USER"]
    db_pass = st.secrets["DB_PASS"]
    db_host = st.secrets["DB_HOST"]
    db_port = st.secrets["DB_PORT"]
    db_name = st.secrets["DB_NAME"]
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

# Inicializar conexión
try:
    engine = get_engine()
    st.sidebar.success("✅ Conexión establecida")
    st.sidebar.page_link("app.py", label="🏠 Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

# --- Lógica de Estado y Filtros ---

# Sidebar - Filtros
st.sidebar.header("🔍 Filtros")

# Filtro de Tipo de Población
selected_population = st.sidebar.radio(
    "Filtrar por tipo de población",
    ["Estudiantes", "Docentes"],
    index=0,
    key="population_filter"
)
population_prefix = "Estudiantes" if selected_population == "Estudiantes" else "Docentes"

@st.cache_data
def get_available_years(_engine, prefix):
    with _engine.connect() as connection:
        query_tables = text(f"SHOW TABLES LIKE '{prefix}_%'")
        result_tables = connection.execute(query_tables)
        return sorted([row[0].split('_')[1] for row in result_tables.fetchall()], reverse=True)

available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning(f"⚠️ No se encontraron datos para '{selected_population}'.")
    st.stop()

# Inicializar el año seleccionado en el estado de la sesión
if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.divider()

# Función para generar gráfico de pastel y tabla
def create_pie_chart_and_table(df_data, total_etapa, title):
    st.header(title)
    
    if df_data.empty:
        st.warning("No hay datos para esta etapa.")
        return

    df_data['cantidad'] = pd.to_numeric(df_data['cantidad'])

    df_pie = df_data.copy()
    if len(df_pie) > 10:
        pie_top = df_pie.nlargest(10, 'cantidad')
        otras_sum = df_pie.nsmallest(len(df_pie) - 10, 'cantidad')['cantidad'].sum()
        pie_top.loc[len(pie_top)] = {'SEDE_NODAL': 'Otras Sedes', 'cantidad': otras_sum}
        df_pie = pie_top

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = plt.cm.viridis(np.linspace(0, 1, len(df_pie)))
    explode = [0.05 if i == 0 else 0 for i in range(len(df_pie))]
    wedges, texts, autotexts = ax.pie(
        df_pie['cantidad'], 
        labels=df_pie['SEDE_NODAL'],
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        explode=explode,
        textprops={'fontsize': 9, 'fontweight': 'bold'},
        shadow=True
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
    
    ax.set_title('Distribución por Sede Nodal', fontsize=14, fontweight='bold', pad=20)
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
    table_name = f"{prefix}_{year}"
    with _engine.connect() as connection:
        query = text(f"""
            SELECT 
                SEDE_NODAL, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE ETAPA = '{stage}'
              AND SEDE_NODAL IS NOT NULL AND SEDE_NODAL != '' AND SEDE_NODAL != 'SIN INFORMACION'
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["SEDE_NODAL", "cantidad"])
        total_matriculados_stage = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE ETAPA = '{stage}'")).scalar() or 0
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
        create_pie_chart_and_table(df_etapa1, total_etapa1, f"📊 Etapa 1 - Año {selected_year}")
    with col2:
        create_pie_chart_and_table(df_etapa2, total_etapa2, f"📊 Etapa 2 - Año {selected_year}")
    
    # --- Botones de Año ---
    st.divider()
    st.markdown("#### Seleccionar otro año")
    cols = st.columns(len(available_years))
    for i, year in enumerate(available_years):
        if cols[i].button(year, key=f"year_btn_{year}", use_container_width=True, type="primary" if year == selected_year else "secondary"):
            st.session_state.selected_year = year
            st.rerun()
    
    st.success(f"""
    ✅ **Datos cargados exitosamente**
    
    📌 **Información del reporte:**
    - **Año**: {selected_year}
    - **Total estudiantes matriculados**: {int(total_matriculados):,}
    - **Matriculados Etapa 1**: {int(total_etapa1):,}
    - **Matriculados Etapa 2**: {int(total_etapa2):,}
    """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())