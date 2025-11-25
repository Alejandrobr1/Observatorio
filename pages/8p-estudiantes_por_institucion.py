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
st.set_page_config(layout="wide", page_title="Estudiantes por Institución")
st.title("📊 Estudiantes por Institución Educativa")

# Inicializar conexión
try:
    engine = get_engine()
    st.sidebar.page_link("app.py", label="Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

# --- Función de Visualización ---
def create_bar_chart_and_table(df_data, total_grupo, title):
    st.header(title)
    
    if df_data.empty:
        st.warning("No hay datos para este grupo.")
        return

    df_data['cantidad'] = pd.to_numeric(df_data['cantidad'])
    df_data = df_data[df_data['cantidad'] > 0]

    if df_data.empty:
        st.info("No hay instituciones con matriculados para este grupo.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_data)))
    bars = ax.bar(df_data['institucion'], df_data['cantidad'], color=colors, edgecolor='black', linewidth=1.2)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height):,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Institución Educativa', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cantidad de Matriculados', fontsize=12, fontweight='bold')
    ax.set_title('Matriculados por Institución', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(rotation=45, ha="right")
    max_val = df_data['cantidad'].max() if not df_data.empty else 1
    ax.set_ylim(0, float(max_val) * 1.2)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("📋 Resumen")
    df_data['porcentaje'] = (df_data['cantidad'] / float(total_grupo) * 100) if total_grupo > 0 else 0
    df_display = df_data.copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
    df_display = df_display[['#', 'institucion', 'cantidad', 'porcentaje']]
    df_display.columns = ['#', 'Institución', 'Matriculados', 'Porcentaje']
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- Consultas y Visualización Principal ---
try:
    with engine.connect() as connection:
        # 1. Obtener años disponibles
        query_years = text("SELECT DISTINCT FECHA FROM Escuela_nueva ORDER BY FECHA DESC")
        result_years = connection.execute(query_years)
        available_years = [row[0] for row in result_years.fetchall()]

        if not available_years:
            st.error("❌ No se encontraron años en la tabla 'Escuela_nueva'.")
            st.stop()

        if 'selected_year' not in st.session_state:
            st.session_state.selected_year = available_years[0] if available_years else None

        selected_year = st.session_state.selected_year

        # 2. Calcular estadísticas para la barra lateral
        st.sidebar.header("📈 Estadísticas Generales")
        table_name = "Escuela_nueva"
        
        query_total = text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE FECHA = :year")
        total_matriculados = connection.execute(query_total, {'year': selected_year}).scalar() or 0
        st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
        
        query_grupo1 = text(f"SELECT SUM(GRUPO_1) FROM {table_name} WHERE FECHA = :year")
        total_grupo1 = connection.execute(query_grupo1, {'year': selected_year}).scalar() or 0
        st.sidebar.metric(f"Matriculados Grupo 1 ({selected_year})", f"{int(total_grupo1):,}")
        
        query_grupo2 = text(f"SELECT SUM(GRUPO_2) FROM {table_name} WHERE FECHA = :year")
        total_grupo2 = connection.execute(query_grupo2, {'year': selected_year}).scalar() or 0
        st.sidebar.metric(f"Matriculados Grupo 2 ({selected_year})", f"{int(total_grupo2):,}")

        query_grupo3 = text(f"SELECT SUM(GRUPO_3) FROM {table_name} WHERE FECHA = :year")
        total_grupo3 = connection.execute(query_grupo3, {'year': selected_year}).scalar() or 0
        st.sidebar.metric(f"Matriculados Grupo 3 ({selected_year})", f"{int(total_grupo3):,}")
        st.sidebar.divider()
        
        # Consultas para cada grupo
        query_grupo1_data = text(f"SELECT INSTITUCION_EDUCATIVA as institucion, COALESCE(SUM(GRUPO_1), 0) as cantidad FROM {table_name} WHERE FECHA = :year AND INSTITUCION_EDUCATIVA IS NOT NULL AND INSTITUCION_EDUCATIVA != '' AND INSTITUCION_EDUCATIVA != 'SIN INFORMACION' GROUP BY institucion ORDER BY cantidad DESC")
        df_grupo1 = pd.DataFrame(connection.execute(query_grupo1_data, {'year': selected_year}).fetchall(), columns=["institucion", "cantidad"])

        query_grupo2_data = text(f"SELECT INSTITUCION_EDUCATIVA as institucion, COALESCE(SUM(GRUPO_2), 0) as cantidad FROM {table_name} WHERE FECHA = :year AND INSTITUCION_EDUCATIVA IS NOT NULL AND INSTITUCION_EDUCATIVA != '' AND INSTITUCION_EDUCATIVA != 'SIN INFORMACION' GROUP BY institucion ORDER BY cantidad DESC")
        df_grupo2 = pd.DataFrame(connection.execute(query_grupo2_data, {'year': selected_year}).fetchall(), columns=["institucion", "cantidad"])

        query_grupo3_data = text(f"SELECT INSTITUCION_EDUCATIVA as institucion, COALESCE(SUM(GRUPO_3), 0) as cantidad FROM {table_name} WHERE FECHA = :year AND INSTITUCION_EDUCATIVA IS NOT NULL AND INSTITUCION_EDUCATIVA != '' AND INSTITUCION_EDUCATIVA != 'SIN INFORMACION' GROUP BY institucion ORDER BY cantidad DESC")
        df_grupo3 = pd.DataFrame(connection.execute(query_grupo3_data, {'year': selected_year}).fetchall(), columns=["institucion", "cantidad"])

        # Layout de tres columnas
        col1, col2, col3 = st.columns(3)
        with col1:
            create_bar_chart_and_table(df_grupo1, total_grupo1, f"📊 Grupo 1 - Año {selected_year}")
        with col2:
            create_bar_chart_and_table(df_grupo2, total_grupo2, f"📊 Grupo 2 - Año {selected_year}")
        with col3:
            create_bar_chart_and_table(df_grupo3, total_grupo3, f"📊 Grupo 3 - Año {selected_year}")
        
        # --- Selección de Año con Botones ---
        st.divider()
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
        - **Total estudiantes matriculados**: {int(total_matriculados):,}
        - **Matriculados Grupo 1**: {int(total_grupo1):,}
        - **Matriculados Grupo 2**: {int(total_grupo2):,}
        - **Matriculados Grupo 3**: {int(total_grupo3):,}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())