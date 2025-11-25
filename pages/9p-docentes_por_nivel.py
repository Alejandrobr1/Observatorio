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
st.title("📊 Docentes por Nivel")

# Inicializar conexión
try:
    engine = get_engine()
    st.sidebar.page_link("app.py", label="Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

# Función para generar gráfico de dona y tabla
def create_donut_chart_and_table(df_data, total_docentes, title):
    st.header(f"📊 {title} - Año {selected_year}")
    
    if df_data.empty:
        st.warning("No hay datos de docentes para el año seleccionado.")
        return

    df_data['cantidad'] = pd.to_numeric(df_data['cantidad'])
    df_data = df_data[df_data['cantidad'] > 0]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Resumen por Nivel")
        df_data['porcentaje'] = (df_data['cantidad'] / float(total_docentes) * 100) if total_docentes > 0 else 0
        df_display = df_data.copy()
        df_display['#'] = range(1, len(df_display) + 1)
        df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
        df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
        df_display = df_display[['#', 'NIVEL', 'cantidad', 'porcentaje']]
        df_display.columns = ['#', 'Nivel', 'Docentes', 'Porcentaje']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Visualización")
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Gráfico de Dona
        labels = df_data['NIVEL']
        sizes = df_data['cantidad']
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(labels)))
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                          colors=colors, pctdistance=0.85,
                                          wedgeprops=dict(width=0.4, edgecolor='w'))
        
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.set_title("Distribución de Docentes por Nivel", pad=20)
        
        # Círculo central para hacer la dona
        centre_circle = plt.Circle((0,0),0.60,fc='white')
        fig.gca().add_artist(centre_circle)
        
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.tight_layout()
        st.pyplot(fig)


# Consultas principales
try:
    with engine.connect() as connection:
        # 1. Obtener años disponibles
        query_years = text("SELECT DISTINCT FECHA FROM Docentes ORDER BY FECHA DESC")
        result_years = connection.execute(query_years)
        available_years = [row[0] for row in result_years.fetchall()]

        if not available_years:
            st.error("❌ No se encontraron años en la columna 'FECHA' de la tabla 'Docentes'.")
            st.stop()

        if 'selected_year' not in st.session_state:
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
        
        # Consulta para Docentes por Nivel
        query_docentes_data = text(f"""
            SELECT 
                NIVEL,
                COUNT(ID) as cantidad
            FROM {table_name}
            WHERE FECHA = :year
              AND NIVEL IS NOT NULL 
              AND NIVEL != '' 
              AND NIVEL != 'SIN INFORMACION'
            GROUP BY NIVEL
            ORDER BY cantidad DESC
        """)
        result_docentes = connection.execute(query_docentes_data, {'year': selected_year})
        df_docentes = pd.DataFrame(result_docentes.fetchall(), columns=["NIVEL", "cantidad"])

        # Crear visualización
        create_donut_chart_and_table(df_docentes, total_docentes, "Distribución de Docentes por Nivel")

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
        - **Total de docentes registrados**: {int(total_docentes):,}
        - **Total de instituciones con docentes**: {int(total_instituciones):,}
        """)

except Exception as e:
    st.error(f"❌ Error al cargar los datos para el año {selected_year}")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
