import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import text
import sys
import os

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Base_datos.conexion import get_engine

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Estudiantes por Sede")
st.title("📊 Estudiantes por Sede")

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
        return sorted([row[0].split('_')[1] for row in result_tables.fetchall()], reverse=True)

# --- Lógica de Estado y Filtros ---
selected_population = "Estudiantes" # Fijo para este reporte
population_prefix = "Estudiantes"

available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning(f"⚠️ No se encontraron datos para '{selected_population}'.")
    st.stop()

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
        query = text(f"""
            SELECT 
                SEDE_NODAL,
                COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE SEDE_NODAL IS NOT NULL AND SEDE_NODAL != '' AND SEDE_NODAL != 'SIN INFORMACION'
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["SEDE_NODAL", "cantidad"])
        
        total_matriculados = df['cantidad'].sum()
        total_sedes = len(df)
        
        return df, total_matriculados, total_sedes

try:
    df, total_matriculados, total_sedes = load_data(engine, population_prefix, selected_year)

    if df.empty:
        st.warning(f"⚠️ No hay datos de estudiantes por sede para el año {selected_year}.")
    else:
        st.sidebar.header("📈 Estadísticas Generales")
        st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{int(total_matriculados):,}")
        st.sidebar.metric(f"Total Sedes ({selected_year})", f"{total_sedes:,}")
        st.sidebar.divider()

        st.header(f"📊 Cantidad de Estudiantes por Sede - Año {selected_year}")
        
        df['cantidad'] = pd.to_numeric(df['cantidad'])
        df_sorted = df.sort_values('cantidad', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(df_sorted) * 0.4)))
        y_pos = np.arange(len(df_sorted))
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_sorted)))
        bars = ax.barh(y_pos, df_sorted['cantidad'], color=colors, edgecolor='black', linewidth=1.2)
        
        for bar in bars:
            width = bar.get_width()
            ax.text(width + (df_sorted['cantidad'].max() * 0.01), bar.get_y() + bar.get_height()/2, f'{int(width):,}', ha='left', va='center')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_sorted['SEDE_NODAL'])
        ax.set_xlabel('Cantidad de Estudiantes')
        ax.set_title('Estudiantes por Sede')
        ax.grid(axis='x', linestyle='--', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig)

        # --- Selección de Año con Botones ---
        st.divider()
        with st.expander("📅 **Seleccionar Año para Visualizar**", expanded=True):
            cols = st.columns(len(available_years))
            def set_year(year):
                st.session_state.selected_year = year

            for i, year in enumerate(available_years):
                with cols[i]:
                    button_type = "primary" if year == selected_year else "secondary"
                    st.button(year, key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

        st.header("📋 Tabla Detallada por Sede")
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())