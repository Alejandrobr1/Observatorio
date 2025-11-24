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
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Población")
st.title("📊 Estudiantes Matriculados por Población")

@st.cache_resource
def get_engine():
    try:
        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))
        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))
        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))
        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))
        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))
    except FileNotFoundError:
        db_user = os.getenv('DB_USER', 'root')
        db_pass = os.getenv('DB_PASS', '123456')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '3308')
        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

# Inicializar conexión
try:
    engine = get_engine()
    st.sidebar.success("✅ Conexión establecida")
    st.sidebar.page_link("app.py", label="🏠 Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

# Sidebar - Filtros
st.sidebar.header("🔍 Filtros")

with engine.connect() as connection:
    # Obtener años disponibles buscando tablas Estudiantes_XXXX
    query_tables = text("SHOW TABLES LIKE 'Estudiantes_%'")
    result_tables = connection.execute(query_tables)
    available_years = sorted([row[0].split('_')[1] for row in result_tables.fetchall()], reverse=True)

    if not available_years:
        st.error("❌ No se encontraron tablas de estudiantes por año (ej. 'Estudiantes_2016').")
        st.stop()

    # Filtro de año
    selected_year = st.sidebar.selectbox(
        '📅 Año',
        available_years,
        index=0,
        help="Selecciona el año para visualizar los datos."
    )

st.sidebar.divider()

# Información general
st.sidebar.header("📈 Estadísticas Generales")

with engine.connect() as connection:
    # Construir el nombre de la tabla dinámicamente
    table_name = f"Estudiantes_{selected_year}"
    
    # Total matriculados
    query_total = text(f"SELECT SUM(MATRICULADOS) FROM {table_name}")
    total_matriculados = connection.execute(query_total).scalar() or 0
    st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
    
    # Total tipos de población
    query_poblacion = text(f"SELECT COUNT(DISTINCT POBLACION) FROM {table_name} WHERE POBLACION IS NOT NULL AND POBLACION != '' AND POBLACION != 'SIN INFORMACION'")
    total_poblacion = connection.execute(query_poblacion).scalar() or 0
    st.sidebar.metric(f"Total Tipos de Población ({selected_year})", f"{total_poblacion:,}")

st.sidebar.divider()

# Consulta principal
try:
    with engine.connect() as connection:
        table_name = f"Estudiantes_{selected_year}"
        
        # Consulta para obtener matriculados por tipo de población
        query = text(f"""
            SELECT 
                POBLACION,
                COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE POBLACION IS NOT NULL 
              AND POBLACION != '' 
              AND POBLACION != 'SIN INFORMACION'
            GROUP BY POBLACION
            ORDER BY cantidad DESC
        """)
        
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["POBLACION", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos de matriculados por población para el año {selected_year}.")
            st.stop()

        # Crear gráfico de barras verticales
        st.header(f"📊 Matriculados por Tipo de Población - Año {selected_year}")
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Colores para las barras
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df)))
        
        bars = ax.bar(df['POBLACION'], df['cantidad'], color=colors, edgecolor='black', linewidth=1.2)
        
        # Agregar etiquetas en las barras
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height):,}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Configuración del gráfico
        ax.set_xlabel('Tipo de Población', fontsize=13, fontweight='bold')
        ax.set_ylabel('Cantidad de Estudiantes Matriculados', fontsize=13, fontweight='bold')
        ax.set_title(f'Estudiantes Matriculados por Tipo de Población\nAño {selected_year}',
                     fontsize=16, fontweight='bold', pad=20)
        plt.xticks(rotation=45, ha="right")
        
        # Configurar límite del eje Y y prevenir error de tipo
        max_val = df['cantidad'].max() if not df.empty else 1
        ax.set_ylim(0, float(max_val) * 1.2)
        
        # Grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig)

        # Tabla de datos detallada
        st.header("📋 Tabla Detallada por Población")
        
        # Calcular porcentajes
        df['porcentaje'] = (pd.to_numeric(df['cantidad']) / float(total_matriculados) * 100) if total_matriculados > 0 else 0
        
        # Formatear para visualización
        df_display = df.copy()
        df_display['#'] = range(1, len(df_display) + 1)
        df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
        df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.1f}%")
        df_display = df_display[['#', 'POBLACION', 'cantidad', 'porcentaje']]
        df_display.columns = ['#', 'Población', 'Matriculados', 'Porcentaje']
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes matriculados**: {int(total_matriculados):,}
        - **Total tipos de población**: {total_poblacion}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())