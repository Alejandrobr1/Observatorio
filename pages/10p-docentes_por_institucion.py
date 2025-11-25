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
st.set_page_config(layout="wide", page_title="Docentes por Institución")
st.title("📊 Docentes por Institución Educativa")

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

# --- Carga de Datos ---
@st.cache_data
def load_data(_engine):
    with _engine.connect() as connection:
        query = text("""
            SELECT 
                i.NOMBRE_INSTITUCION,
                COUNT(d.ID_DOCENTE) as cantidad
            FROM Docentes d
            JOIN Instituciones i ON d.ID_INSTITUCION = i.ID_INSTITUCION
            GROUP BY i.NOMBRE_INSTITUCION
            ORDER BY cantidad DESC;
        """)
        try:
            result = connection.execute(query)
            df = pd.DataFrame(result.fetchall(), columns=["INSTITUCION", "cantidad"])
            total_docentes = df['cantidad'].sum()
            total_instituciones = len(df)
            return df, total_docentes, total_instituciones
        except Exception as e:
            # Manejar el caso donde las tablas no existen
            if "doesn't exist" in str(e):
                return pd.DataFrame(columns=["INSTITUCION", "cantidad"]), 0, 0
            raise e

try:
    df, total_docentes, total_instituciones = load_data(engine)

    if df.empty:
        st.warning("⚠️ No se encontraron datos de docentes por institución. Verifique que las tablas 'Docentes' e 'Instituciones' existan y contengan datos.")
    else:
        st.sidebar.header("📈 Estadísticas Generales")
        st.sidebar.metric("Total Docentes", f"{int(total_docentes):,}")
        st.sidebar.metric("Total Instituciones", f"{total_instituciones:,}")
        st.sidebar.divider()

        st.header("📊 Cantidad de Docentes por Institución")
        
        df['cantidad'] = pd.to_numeric(df['cantidad'])
        df_sorted = df.sort_values('cantidad', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(df_sorted) * 0.4)))
        y_pos = np.arange(len(df_sorted))
        colors = plt.cm.magma(np.linspace(0.3, 0.9, len(df_sorted)))
        bars = ax.barh(y_pos, df_sorted['cantidad'], color=colors, edgecolor='black', linewidth=1.2)
        
        for bar in bars:
            width = bar.get_width()
            ax.text(width + (df_sorted['cantidad'].max() * 0.01), bar.get_y() + bar.get_height()/2, f'{int(width):,}', ha='left', va='center')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_sorted['INSTITUCION'])
        ax.set_xlabel('Cantidad de Docentes')
        ax.set_title('Docentes por Institución Educativa')
        ax.grid(axis='x', linestyle='--', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig)

        st.divider()
        st.header("📋 Tabla Detallada por Institución")
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
