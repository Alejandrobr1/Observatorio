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
    st.sidebar.page_link("app.py", label="Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

            st.session_state.selected_year = available_years[0] if available_years else None

        selected_year = st.session_state.selected_year

        # 2. Calcular estadísticas para la barra lateral
        st.sidebar.header("📈 Estadísticas Generales")
        table_name = "Docentes"
        
        query_total = text(f"SELECT COUNT(ID) FROM {table_name} WHERE FECHA = :year")
        total_docentes = connection.execute(query_total, {'year': selected_year}).scalar() or 0
        st.sidebar.metric(f"Total Docentes ({selected_year})", f"{int(total_docentes):,}")
        
        query_instituciones = text(f"SELECT COUNT(DISTINCT INSTITUCION_EDUCATIVA) FROM {table_name} WHERE FECHA = :year")
        total_instituciones = connection.execute(query_instituciones, {'year': selected_year}).scalar() or 0
        st.sidebar.metric(f"Instituciones con Docentes ({selected_year})", f"{int(total_instituciones):,}")
        st.sidebar.divider()
        
        # Consulta para Docentes por Institución
        query_docentes_data = text(f"""
            SELECT 
                INSTITUCION_EDUCATIVA as institucion,
                COUNT(ID) as cantidad
            FROM {table_name}
            WHERE FECHA = :year
              AND INSTITUCION_EDUCATIVA IS NOT NULL 
              AND INSTITUCION_EDUCATIVA != '' 
              AND INSTITUCION_EDUCATIVA != 'SIN INFORMACION'
            GROUP BY institucion
            ORDER BY cantidad DESC
        """)
        result_docentes = connection.execute(query_docentes_data, {'year': selected_year})
        df_docentes = pd.DataFrame(result_docentes.fetchall(), columns=["institucion", "cantidad"])

        # Crear visualización
        create_bar_chart_and_table(df_docentes, total_docentes, "Distribución de Docentes por Institución")
        
        # --- Selección de Año con Botones ---
        st.sidebar.divider()
        with st.expander("📅 **Seleccionar Año para Visualizar**", expanded=True):
            st.write("Haz clic en un botón para cambiar el año de los datos mostrados.")
            
            cols = st.columns(len(available_years))
            
            def set_year(year):
                st.session_state.selected_year = year

            for i, year in enumerate(available_years):
                with cols[i]:
                    button_type = "primary" if str(year) == str(selected_year) else "secondary"
                    if st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,)):
                        pass

        # Información adicional
        st.success(f"""
        ✅ **Datos cargados para el año {selected_year}**
        
        📌 **Información del reporte:**
        - **Total de docentes registrados**: {int(total_docentes):,}
        - **Total de instituciones con docentes**: {int(total_instituciones):,}
        """)

except Exception as e:
    st.error(f"❌ Error al cargar los datos para el año {selected_year}")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
