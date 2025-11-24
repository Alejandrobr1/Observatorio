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
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Jornada y Día")
st.title("📊 Estudiantes Matriculados por Jornada y Día")

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

# Filtro de Año
selected_year = st.sidebar.selectbox(
    'Seleccionar Año',
    available_years,
    index=0,
    key='year_filter'
)
st.sidebar.divider()

# --- Carga de Datos ---
@st.cache_data
def load_data(_engine, year, prefix):
    table_name = f"{prefix}_{year}"
    with _engine.connect() as connection:
        query = text(f"""
            SELECT 
                DIA, JORNADA, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE DIA IS NOT NULL AND DIA != '' AND DIA != 'SIN INFORMACION'
              AND JORNADA IS NOT NULL AND JORNADA != '' AND JORNADA != 'SIN INFORMACION'
            GROUP BY DIA, JORNADA
            ORDER BY DIA, JORNADA
        """)
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["DIA", "JORNADA", "cantidad"])
        
        # Métricas
        total_matriculados = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name}")).scalar() or 0
        total_jornadas = connection.execute(text(f"SELECT COUNT(DISTINCT JORNADA) FROM {table_name} WHERE JORNADA IS NOT NULL AND JORNADA != ''")).scalar() or 0
        total_dias = connection.execute(text(f"SELECT COUNT(DISTINCT DIA) FROM {table_name} WHERE DIA IS NOT NULL AND DIA != ''")).scalar() or 0
        
        return df, total_matriculados, total_jornadas, total_dias

try:
    df, total_matriculados, total_jornadas, total_dias = load_data(engine, selected_year, population_prefix)

    # --- Visualización ---
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
    st.sidebar.metric(f"Total Jornadas ({selected_year})", f"{total_jornadas:,}")
    st.sidebar.metric(f"Total Días ({selected_year})", f"{total_dias:,}")
    st.sidebar.divider()

    if df.empty:
        st.warning(f"⚠️ No hay datos de matriculados por jornada y día para el año {selected_year}.")
    else:
        # Pivotear los datos para tener días como índice y jornadas como columnas
        df_pivot = df.pivot(index='DIA', columns='JORNADA', values='cantidad').fillna(0)

        # Crear gráfico de barras verticales agrupadas
        st.header(f"📊 Matriculados por Jornada y Día - Año {selected_year}")
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
        ax.set_title(f'Estudiantes Matriculados por Jornada y Día\nAño {selected_year}',
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(dias, rotation=45, ha='right', fontsize=11)
        ax.legend(title='Jornada', fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        max_val = df_pivot.sum(axis=1).max()
        ax.set_ylim(0, float(max_val) * 1.2)
        plt.tight_layout()
        st.pyplot(fig)

        # Tabla de datos detallada
        st.header("📋 Tabla Detallada")
        df_display = df_pivot.copy()
        df_display = df_display.astype(int).applymap('{:,}'.format)
        df_display['Total por Día'] = df_pivot.sum(axis=1).astype(int).apply('{:,}'.format)
        st.dataframe(df_display, use_container_width=True)
        
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes matriculados**: {int(total_matriculados):,}
        - **Total jornadas**: {total_jornadas}
        - **Total días**: {total_dias}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
