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
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Etapa y Sede")
st.title("📊 Comparativa de Estudiantes por Etapa y Sede")

@st.cache_resource
def get_engine():
    # Lee desde st.secrets
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
    # No mostrar mensaje de éxito, es redundante.
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
    with _engine.connect() as connection:
        if prefix == "Estudiantes":
            if _engine.dialect.has_table(connection, table_name):
                query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} ORDER BY FECHA DESC")
                years = [row[0] for row in connection.execute(query_years).fetchall()]
                if years:
                    return years
                st.warning(f"La tabla '{table_name}' no contiene años en la columna 'FECHA'. Usando año por defecto.")
                return [pd.Timestamp.now().year]
        else: # Para Docentes
            query_tables = text(f"SHOW TABLES LIKE '{prefix}_%'")
            years = []
            for row in connection.execute(query_tables).fetchall():
                parts = row[0].split('_')
                if len(parts) > 1 and parts[1].isdigit():
                    years.append(parts[1])
            if years:
                return sorted(list(set(years)), reverse=True)
    return []

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

# FORZAR REINICIO DEL AÑO: Si el año guardado en la sesión no es válido para
# los datos de ESTA PÁGINA, se reinicia al año más reciente disponible.
if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.header("🔍 Filtros Aplicados")
st.sidebar.info(f"**Población:** {selected_population}")
st.sidebar.info(f"**Año:** {selected_year}")
st.sidebar.divider()

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
    
    # Unir los dataframes para el gráfico de barras agrupadas
    df_merged = pd.merge(df_etapa1, df_etapa2, on='SEDE_NODAL', how='outer', suffixes=('_e1', '_e2')).fillna(0)
    df_merged = df_merged.rename(columns={'cantidad_e1': 'Etapa 1', 'cantidad_e2': 'Etapa 2'})
    df_merged['Total'] = df_merged['Etapa 1'] + df_merged['Etapa 2']
    df_merged = df_merged.sort_values('Total', ascending=False)

    if df_merged.empty:
        st.warning(f"⚠️ No hay datos de matriculados por sede nodal para el año {selected_year}.")
    else:
        st.header(f"📊 Comparativa de Matriculados por Etapa y Sede Nodal - Año {selected_year}")
        fig, ax = plt.subplots(figsize=(14, 8))
        
        sedes = df_merged['SEDE_NODAL']
        n_sedes = len(sedes)
        x = np.arange(n_sedes)
        width = 0.4

        bars1 = ax.bar(x - width/2, df_merged['Etapa 1'], width, label='Etapa 1', color='skyblue', edgecolor='black')
        bars2 = ax.bar(x + width/2, df_merged['Etapa 2'], width, label='Etapa 2', color='lightcoral', edgecolor='black')

        def add_labels(bars):
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{int(height):,}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        add_labels(bars1)
        add_labels(bars2)

        ax.set_xlabel('Sede Nodal', fontsize=13, fontweight='bold')
        ax.set_ylabel('Cantidad de Estudiantes Matriculados', fontsize=13, fontweight='bold')
        ax.set_title(f'Estudiantes Matriculados por Etapa y Sede Nodal\nAño {selected_year}',
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(sedes, rotation=45, ha='right', fontsize=10)
        ax.legend(title='Etapa', fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        max_val = df_merged[['Etapa 1', 'Etapa 2']].max().max()
        ax.set_ylim(0, float(max_val) * 1.2)
        plt.tight_layout()
        st.pyplot(fig)

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