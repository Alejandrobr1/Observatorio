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
st.set_page_config(layout="wide", page_title="Dashboard Participación por Etapa y Sede Nodal")
st.title("📊 Participación por Etapa y Sede Nodal")

@st.cache_resource
def get_engine():
    # En producción (Streamlit Cloud), lee desde st.secrets
    db_user = st.secrets["DB_USER"]
    db_pass = st.secrets["DB_PASS"]
    db_host = st.secrets["DB_HOST"]
    db_port = st.secrets["DB_PORT"]
    db_name = st.secrets["DB_NAME"]
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
    
    # Total matriculados Etapa 1
    query_etapa1 = text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE ETAPA = '1'")
    total_etapa1 = connection.execute(query_etapa1).scalar() or 0
    st.sidebar.metric(f"Matriculados Etapa 1 ({selected_year})", f"{int(total_etapa1):,}")
    
    # Total matriculados Etapa 2
    query_etapa2 = text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE ETAPA = '2'")
    total_etapa2 = connection.execute(query_etapa2).scalar() or 0
    st.sidebar.metric(f"Matriculados Etapa 2 ({selected_year})", f"{int(total_etapa2):,}")

st.sidebar.divider()

# Función para generar gráfico de pastel y tabla
def create_pie_chart_and_table(df_data, total_etapa, title):
    st.header(title)
    
    if df_data.empty:
        st.warning("No hay datos para esta etapa.")
        return

    # Convertir cantidad a numérico para evitar errores de tipo
    df_data['cantidad'] = pd.to_numeric(df_data['cantidad'])

    # Agrupar las sedes más pequeñas en "Otras" para mejorar la visualización
    df_pie = df_data.copy()
    if len(df_pie) > 10:
        pie_top = df_pie.nlargest(10, 'cantidad')
        otras_sum = df_pie.nsmallest(len(df_pie) - 10, 'cantidad')['cantidad'].sum()
        pie_top.loc[len(pie_top)] = {'SEDE_NODAL': 'Otras Sedes', 'cantidad': otras_sum}
        df_pie = pie_top

    # Crear el gráfico de pastel
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = plt.cm.viridis(np.linspace(0, 1, len(df_pie)))
    explode = [0.05 if i == 0 else 0 for i in range(len(df_pie))]
    
    wedges, texts, autotexts = ax.pie(
        df_pie['cantidad'], 
        labels=df_pie['SEDE_NODAL'],
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        explode=explode,
        textprops={'fontsize': 9, 'fontweight': 'bold'},
        shadow=True
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
    
    ax.set_title('Distribución por Sede Nodal', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    st.pyplot(fig)

    # Crear la tabla de resumen
    st.subheader("📋 Resumen")
    df_data['porcentaje'] = (df_data['cantidad'] / float(total_etapa) * 100) if total_etapa > 0 else 0
    
    df_display = df_data.copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.1f}%")
    df_display = df_display[['#', 'SEDE_NODAL', 'cantidad', 'porcentaje']]
    df_display.columns = ['#', 'Sede Nodal', 'Matriculados', 'Porcentaje']
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# Consultas principales
try:
    with engine.connect() as connection:
        table_name = f"Estudiantes_{selected_year}"
        
        # Consulta para Etapa 1
        query_etapa1_data = text(f"""
            SELECT 
                SEDE_NODAL,
                COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE ETAPA = '1'
              AND SEDE_NODAL IS NOT NULL 
              AND SEDE_NODAL != '' 
              AND SEDE_NODAL != 'SIN INFORMACION'
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        result_etapa1 = connection.execute(query_etapa1_data)
        df_etapa1 = pd.DataFrame(result_etapa1.fetchall(), columns=["SEDE_NODAL", "cantidad"])

        # Consulta para Etapa 2
        query_etapa2_data = text(f"""
            SELECT 
                SEDE_NODAL,
                COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE ETAPA = '2'
              AND SEDE_NODAL IS NOT NULL 
              AND SEDE_NODAL != '' 
              AND SEDE_NODAL != 'SIN INFORMACION'
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        result_etapa2 = connection.execute(query_etapa2_data)
        df_etapa2 = pd.DataFrame(result_etapa2.fetchall(), columns=["SEDE_NODAL", "cantidad"])

        # Crear layout de dos columnas
        col1, col2 = st.columns(2)

        with col1:
            create_pie_chart_and_table(df_etapa1, total_etapa1, f"📊 Etapa 1 - Año {selected_year}")

        with col2:
            create_pie_chart_and_table(df_etapa2, total_etapa2, f"📊 Etapa 2 - Año {selected_year}")
        
        # Información adicional
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes matriculados**: {int(total_matriculados):,}
        - **Matriculados Etapa 1**: {int(total_etapa1):,}
        - **Matriculados Etapa 2**: {int(total_etapa2):,}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())