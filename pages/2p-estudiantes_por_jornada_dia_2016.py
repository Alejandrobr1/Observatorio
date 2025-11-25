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
    st.sidebar.page_link("app.py", label="Volver al Inicio", icon="🏠")
    st.sidebar.divider()
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
            # Verificar si la tabla consolidada existe
            inspector = _engine.dialect.has_table(connection, table_name)
            if inspector:
                query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} ORDER BY FECHA DESC")
                result_years = connection.execute(query_years)
                return [row[0] for row in result_years.fetchall()]
    return [] # Retorna vacío si no es 'Estudiantes' o la tabla no existe

col1, col2 = st.columns([1, 3])
with col1:
    selected_population = st.selectbox(
        "Filtrar por tipo de población",
        ["Estudiantes", "Docentes"],
        key="population_filter",
        help="Selecciona si quieres ver datos de Estudiantes o Docentes."
    )

population_prefix = "Estudiantes" if selected_population == "Estudiantes" else "Docentes"
available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning(f"⚠️ No se encontraron datos para '{selected_population}'.")
    st.stop()

# Inicializar el estado de la sesión para el año si no existe o si cambió la población
if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.header("🔍 Filtros Aplicados")
st.sidebar.info(f"**Población:** {selected_population}")
st.sidebar.info(f"**Año:** {selected_year}")
st.sidebar.divider()

# --- Carga de Datos ---
@st.cache_data
def load_data(_engine, prefix, year):
    # Si son estudiantes, usar la tabla consolidada. Si no, mantener la lógica anterior.
    table_name = "Estudiantes_2016_2019" if prefix == "Estudiantes" else f"{prefix}_{year}"
    
    # Verificar si la tabla existe antes de consultarla
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(columns=["DIA", "JORNADA", "cantidad"]), 0, 0, 0

    with _engine.connect() as connection:
        query = text(f"""
            SELECT 
                DIA, JORNADA, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE DIA IS NOT NULL AND DIA != '' AND DIA != 'SIN INFORMACION'
              AND JORNADA IS NOT NULL AND JORNADA != '' AND JORNADA != 'SIN INFORMACION'
              AND ETAPA = '1'
              AND FECHA = :year
            GROUP BY DIA, JORNADA
            ORDER BY DIA, JORNADA
        """)
        result = connection.execute(query, {'year': year})
        df = pd.DataFrame(result.fetchall(), columns=["DIA", "JORNADA", "cantidad"])
        
        # Métricas
        params = {'year': year}
        total_matriculados = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE ETAPA = '1' AND FECHA = :year"), params).scalar() or 0
        total_jornadas = connection.execute(text(f"SELECT COUNT(DISTINCT JORNADA) FROM {table_name} WHERE ETAPA = '1' AND FECHA = :year AND JORNADA IS NOT NULL AND JORNADA != ''"), params).scalar() or 0
        total_dias = connection.execute(text(f"SELECT COUNT(DISTINCT DIA) FROM {table_name} WHERE ETAPA = '1' AND FECHA = :year AND DIA IS NOT NULL AND DIA != ''"), params).scalar() or 0
        
        return df, total_matriculados, total_jornadas, total_dias

try:
    df, total_matriculados, total_jornadas, total_dias = load_data(engine, population_prefix, selected_year)

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

        # --- Selección de Año con Botones ---
        st.divider()
        with st.expander("📅 **Seleccionar Año para Visualizar**", expanded=True):
            st.write("Haz clic en un botón para cambiar el año de los datos mostrados en los gráficos.")
            
            cols = st.columns(len(available_years))
            
            def set_year(year):
                st.session_state.selected_year = year

            for i, year in enumerate(available_years):
                with cols[i]:
                    button_type = "primary" if year == selected_year else "secondary"
                    st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

        # Tabla de datos detallada
        df_display = df_pivot.copy()
        df_display = df_display.astype(int).applymap('{:,}'.format)
        df_display['Total por Día'] = df_pivot.sum(axis=1).astype(int).apply('{:,}'.format)
        st.header("📋 Tabla Detallada")
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
