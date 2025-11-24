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
st.title("📊 Comparativa de Estudiantes por Etapa y Sede Nodal.")

@st.cache_resource
def get_engine():
    # En producción (Streamlit Cloud), lee desde st.secrets
    db_user = st.secrets["DB_USER"]
    db_pass = st.secrets["DB_PASS"]
    db_host = st.secrets["DB_HOST"]
    db_port = st.secrets["DB_PORT"]
    db_name = st.secrets["DB_NAME"]
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string, pool_recycle=1800)

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

# El prefijo ahora está fijo para 'estudiantes'
population_prefix = "estudiantes"

@st.cache_data
def get_available_years(_engine, prefix):
    with _engine.connect() as connection:
        query_tables = text(f"SHOW TABLES LIKE '{prefix.lower()}_%'")
        result_tables = connection.execute(query_tables)
        return sorted([row[0].split('_')[1] for row in result_tables.fetchall()], reverse=True)

available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning("⚠️ No se encontraron datos de estudiantes para ningún año.")
    st.stop()

# Filtro de Año
selected_year = st.sidebar.selectbox(
    'Seleccionar Año',
    available_years,
    index=0,
    key='year_filter'
)
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
        create_bar_chart_and_table(df_etapa1, total_etapa1, f"📊 Etapa 1 - Año {selected_year}")
    with col2:
        create_bar_chart_and_table(df_etapa2, total_etapa2, f"📊 Etapa 2 - Año {selected_year}")
    
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