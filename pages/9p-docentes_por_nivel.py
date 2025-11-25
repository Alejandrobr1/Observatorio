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
st.set_page_config(layout="wide", page_title="Docentes por Nivel")
st.title("📊 Docentes por Nivel Educativo")

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
selected_population = "Docentes" # Fijo para este reporte
population_prefix = "Docentes"

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
        # Asumiendo que la tabla de docentes tiene una columna 'NIVEL' y 'MATRICULADOS' representa el conteo de docentes
        query = text(f"""
            SELECT 
                NIVEL,
                COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE NIVEL IS NOT NULL AND NIVEL != '' AND NIVEL != 'SIN INFORMACION'
            GROUP BY NIVEL
            ORDER BY NIVEL ASC
        """)
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["NIVEL", "cantidad"])
        
        total_docentes = df['cantidad'].sum()
        total_niveles = len(df)
        
        return df, total_docentes, total_niveles

try:
    df, total_docentes, total_niveles = load_data(engine, population_prefix, selected_year)

    if df.empty:
        st.warning(f"⚠️ No hay datos de docentes por nivel para el año {selected_year}.")
    else:
        st.sidebar.header("📈 Estadísticas Generales")
        st.sidebar.metric(f"Total Docentes ({selected_year})", f"{int(total_docentes):,}")
        st.sidebar.metric(f"Total Niveles ({selected_year})", f"{total_niveles:,}")
        st.sidebar.divider()

        st.header(f"📊 Cantidad de Docentes por Nivel - Año {selected_year}")
        
        df['cantidad'] = pd.to_numeric(df['cantidad'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = plt.cm.cividis(np.linspace(0.3, 0.9, len(df)))
        bars = ax.bar(df['NIVEL'].astype(str), df['cantidad'], color=colors, edgecolor='black', linewidth=1.2)
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height):,}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom')

        ax.set_xlabel('Nivel Educativo')
        ax.set_ylabel('Cantidad de Docentes')
        ax.set_title('Docentes por Nivel Educativo')
        ax.grid(axis='y', linestyle='--', alpha=0.6)
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

        st.header("📋 Tabla Detallada por Nivel")
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
