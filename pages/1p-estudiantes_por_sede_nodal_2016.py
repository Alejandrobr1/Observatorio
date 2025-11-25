import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import traceback
from sqlalchemy import text, create_engine
import sys 
import os
import numpy as np

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Sede Nodal")
st.title("📊 Estudiantes Matriculados por Sede Nodal")

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
    st.sidebar.success("✅ Conexión establecida")
    st.sidebar.page_link("app.py", label="Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

@st.cache_data
def get_available_years(_engine, prefix):
    with _engine.connect() as connection:
        query_tables = text(f"SHOW TABLES LIKE '{prefix}_%'")
        result_tables = connection.execute(query_tables)
        years = []
        for row in result_tables.fetchall():
            parts = row[0].split('_')
            if len(parts) > 1 and parts[1].isdigit():
                years.append(parts[1])
        return sorted(years, reverse=True)

# --- Lógica de Estado y Filtros ---

# Selectores en la parte superior
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
    table_name = f"{prefix}_{year}"
    with _engine.connect() as connection:
        # Consulta para obtener estudiantes matriculados por sede nodal
        query = text(f"""
            SELECT 
                SEDE_NODAL,
                COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE SEDE_NODAL IS NOT NULL 
              AND SEDE_NODAL != '' 
              AND SEDE_NODAL != 'SIN INFORMACION'
              AND ETAPA = '1'
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        result = connection.execute(query)
        return pd.DataFrame(result.fetchall(), columns=["SEDE_NODAL", "cantidad"])

try:
    df = load_data(engine, population_prefix, selected_year)

    if df.empty:
        st.warning(f"⚠️ No hay datos de matriculados por sede nodal para el año {selected_year}.")
    else:
        # --- Visualización ---
        
        # Información general
        st.sidebar.header("📈 Estadísticas Generales")
        total_matriculados = pd.to_numeric(df['cantidad']).sum()
        total_sedes = len(df)
        st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
        st.sidebar.metric(f"Total Sedes Nodales ({selected_year})", f"{total_sedes:,}")
        st.sidebar.divider()

        # Crear gráfico de barras horizontales
        st.header(f"📊 Matriculados por Sede Nodal - Año {selected_year}")
        
        df['cantidad'] = pd.to_numeric(df['cantidad'])
        df_sorted = df.sort_values('cantidad', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(df_sorted) * 0.5)))
        y_pos = range(len(df_sorted))
        colors_gradient = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_sorted)))
        bars = ax.barh(y_pos, df_sorted['cantidad'], color=colors_gradient, edgecolor='black', linewidth=1.2)
        
        for i, (bar, valor) in enumerate(zip(bars, df_sorted['cantidad'])):
            ax.text(valor, i, f'  {int(valor):,}', ha='left', va='center', color='black', fontsize=10, fontweight='bold')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_sorted['SEDE_NODAL'], fontsize=10)
        ax.set_xlabel('Cantidad de Estudiantes Matriculados', fontsize=13, fontweight='bold')
        ax.set_ylabel('Sede Nodal', fontsize=13, fontweight='bold')
        ax.set_title(f'Estudiantes Matriculados por Sede Nodal\nAño {selected_year}', fontsize=16, fontweight='bold', pad=20)
        
        max_val = df_sorted['cantidad'].max() if not df_sorted.empty else 1
        ax.set_xlim(0, float(max_val) * 1.15)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
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

        # Tabla resumen
        df['porcentaje'] = (df['cantidad'] / float(total_matriculados) * 100) if total_matriculados > 0 else 0
        df_display = df.copy()
        df_display['#'] = range(1, len(df_display) + 1)
        df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
        df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.1f}%")
        df_display = df_display[['#', 'SEDE_NODAL', 'cantidad', 'porcentaje']]
        df_display.columns = ['#', 'Sede Nodal', 'Matriculados', 'Porcentaje']
        st.header("📋 Tabla Detallada por Sede Nodal")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # --- Información de Éxito ---
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes matriculados**: {int(total_matriculados):,}
        - **Total sedes nodales**: {total_sedes}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
