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
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes Colombo")
st.title("📊 Estudiantes Colombo por Institución Educativa")

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

# Función para generar gráfico de barras y tabla
def create_bar_chart_and_table(df_data, total_estudiantes, title):
    st.header(f"📊 {title} - Año {selected_year}")
    
    if df_data.empty:
        st.warning("No hay datos de estudiantes para el año seleccionado.")
        return

    df_data['cantidad'] = pd.to_numeric(df_data['cantidad'])
    df_data = df_data[df_data['cantidad'] > 0]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Visualización por Institución")
        # Ordenar datos para gráfico horizontal
        df_sorted = df_data.sort_values('cantidad', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, max(6, len(df_sorted) * 0.3)))
        y_pos = np.arange(len(df_sorted))
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_sorted)))
        
        bars = ax.barh(y_pos, df_sorted['cantidad'], color=colors, edgecolor='black', linewidth=1.2)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_sorted['institucion'])
        ax.set_xlabel('Cantidad de Estudiantes')
        ax.set_title('Estudiantes Colombo por Institución Educativa')
        
        # Añadir etiquetas de valor en las barras
        for bar in bars:
            width = bar.get_width()
            ax.text(width + (df_sorted['cantidad'].max() * 0.01), bar.get_y() + bar.get_height()/2,
                    f'{int(width):,}', ha='left', va='center', fontsize=9)
        
        ax.grid(axis='x', linestyle='--', alpha=0.6)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("📋 Resumen")
        df_data['porcentaje'] = (df_data['cantidad'] / float(total_estudiantes) * 100) if total_estudiantes > 0 else 0
        df_display = df_data.copy()
        df_display['#'] = range(1, len(df_display) + 1)
        df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
        df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
        df_display = df_display[['#', 'institucion', 'cantidad', 'porcentaje']]
        df_display.columns = ['#', 'Institución', 'Estudiantes', 'Porcentaje']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# Consultas principales
try:
    with engine.connect() as connection:
        # 1. Obtener años disponibles
        query_years = text("SELECT DISTINCT FECHA FROM Estudiantes_Colombo ORDER BY FECHA DESC")
        result_years = connection.execute(query_years)
        available_years = [row[0] for row in result_years.fetchall()]

        if not available_years:
            st.error("❌ No se encontraron años en la columna 'FECHA' de la tabla 'Estudiantes_Colombo'.")
            st.stop()

        if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
            st.session_state.selected_year = available_years[0] if available_years else None

        selected_year = st.session_state.selected_year

        # 2. Calcular estadísticas para la barra lateral
        st.sidebar.header("📈 Estadísticas Generales")
        table_name = "Estudiantes_Colombo"
        
        query_total = text(f"SELECT COUNT(ID) FROM {table_name} WHERE FECHA = :year")
        total_estudiantes = connection.execute(query_total, {'year': selected_year}).scalar() or 0
        st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{int(total_estudiantes):,}")
        
        query_instituciones = text(f"SELECT COUNT(DISTINCT INSTITUCION_EDUCATIVA) FROM {table_name} WHERE FECHA = :year")
        total_instituciones = connection.execute(query_instituciones, {'year': selected_year}).scalar() or 0
        st.sidebar.metric(f"Instituciones ({selected_year})", f"{int(total_instituciones):,}")
        st.sidebar.divider()
        
        # Consulta para Estudiantes por Institución
        query_estudiantes_data = text(f"""
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
        result_estudiantes = connection.execute(query_estudiantes_data, {'year': selected_year})
        df_estudiantes = pd.DataFrame(result_estudiantes.fetchall(), columns=["institucion", "cantidad"])

        # Crear visualización
        create_bar_chart_and_table(df_estudiantes, total_estudiantes, "Distribución de Estudiantes Colombo por Institución")
        
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
        
        📌 **Información del reporte:**
        - **Total de estudiantes registrados**: {int(total_estudiantes):,}
        - **Total de instituciones con estudiantes**: {int(total_instituciones):,}
        """)

except Exception as e:
    st.error(f"❌ Error al cargar los datos para el año {selected_year}")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())