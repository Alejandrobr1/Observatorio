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

# --- Lógica de Estado y Filtros ---
selected_population = "Estudiantes" # Fijo para este reporte

st.sidebar.header("🔍 Filtros Aplicados")
st.sidebar.info(f"**Población:** {selected_population}")
st.sidebar.divider()

# --- Carga de Datos ---
@st.cache_data
def load_data(_engine):
    with _engine.connect() as connection:
        query = text("""
            SELECT 
                SEDE,
                COUNT(*) as cantidad
            FROM Estudiantes_escuela
            WHERE SEDE IS NOT NULL AND SEDE != '' AND SEDE != 'SIN INFORMACION'
            GROUP BY SEDE
            ORDER BY cantidad DESC
        """)
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["SEDE", "cantidad"])
        
        total_matriculados = df['cantidad'].sum()
        total_sedes = len(df)
        
        return df, total_matriculados, total_sedes

try:
    df, total_matriculados, total_sedes = load_data(engine)

    if df.empty:
        st.warning("⚠️ No hay datos de estudiantes por sede. Verifique que la tabla 'Estudiantes_escuela' exista y contenga datos.")
    else:
        st.sidebar.header("📈 Estadísticas Generales")
        st.sidebar.metric(f"Total Registros", f"{int(total_matriculados):,}")
        st.sidebar.metric(f"Total Sedes", f"{total_sedes:,}")
        st.sidebar.divider()

        st.header(f"📊 Cantidad de Registros por Sede")
        
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
        ax.set_yticklabels(df_sorted['SEDE'])
        ax.set_xlabel('Cantidad de Registros')
        ax.set_title('Registros por Sede')
        ax.grid(axis='x', linestyle='--', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig)

        st.header("📋 Tabla Detallada por Sede")
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())