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
st.set_page_config(layout="wide", page_title="Dashboard Participación por Sede Nodal")
st.title("📊 Participación de Estudiantes por Sede Nodal")

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
    
    # Total sedes nodales
    query_sedes = text(f"SELECT COUNT(DISTINCT SEDE_NODAL) FROM {table_name} WHERE SEDE_NODAL IS NOT NULL AND SEDE_NODAL != '' AND SEDE_NODAL != 'SIN INFORMACION'")
    total_sedes = connection.execute(query_sedes).scalar() or 0
    st.sidebar.metric(f"Total Sedes Nodales ({selected_year})", f"{total_sedes:,}")

st.sidebar.divider()

# Consulta principal
try:
    with engine.connect() as connection:
        table_name = f"Estudiantes_{selected_year}"
        
        # Consulta para obtener matriculados por sede nodal
        query = text(f"""
            SELECT 
                SEDE_NODAL,
                COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE SEDE_NODAL IS NOT NULL 
              AND SEDE_NODAL != '' 
              AND SEDE_NODAL != 'SIN INFORMACION'
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["SEDE_NODAL", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos de matriculados por sede nodal para el año {selected_year}.")
            st.stop()

        # Convertir cantidad a numérico para evitar errores de tipo
        df['cantidad'] = pd.to_numeric(df['cantidad'])
        
        # Mostrar estadísticas en sidebar
        st.sidebar.header(f"📊 Top 5 Sedes Nodales - {selected_year}")
        top_5 = df.head(5)
        for idx, row in top_5.iterrows():
            nombre_sede = row['SEDE_NODAL']
            total = row['cantidad']
            nombre_corto = nombre_sede[:30] + '...' if len(nombre_sede) > 30 else nombre_sede
            st.sidebar.write(f"**{idx+1}. {nombre_corto}**")
            st.sidebar.write(f"   {int(total):,} matriculados")

        # Crear gráfico de pastel principal
        st.header(f"📊 Distribución de Matriculados por Sede Nodal - Año {selected_year}")
        
        # Agrupar las sedes más pequeñas en "Otras" para mejorar la visualización
        df_pie = df.copy()
        if len(df_pie) > 10:
            pie_top = df_pie.nlargest(10, 'cantidad')
            otras_sum = df_pie.nsmallest(len(df_pie) - 10, 'cantidad')['cantidad'].sum()
            pie_top.loc[len(pie_top)] = {'SEDE_NODAL': 'Otras Sedes', 'cantidad': otras_sum}
            df_pie = pie_top
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            colors = plt.cm.viridis(np.linspace(0, 1, len(df_pie)))
            explode = [0.05 if i == 0 else 0 for i in range(len(df_pie))]
            
            wedges, texts, autotexts = ax.pie(
                df_pie['cantidad'], 
                labels=df_pie['SEDE_NODAL'],
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                explode=explode,
                textprops={'fontsize': 10, 'fontweight': 'bold'},
                shadow=True
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
            
            ax.set_title(f'Participación por Sede Nodal\nAño {selected_year}', 
                        fontsize=18, fontweight='bold', pad=20)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.subheader("📋 Resumen")
            
            df['porcentaje'] = (df['cantidad'] / float(total_matriculados) * 100) if total_matriculados > 0 else 0
            
            df_display = df.copy()
            df_display['#'] = range(1, len(df_display) + 1)
            df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
            df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.1f}%")
            df_display = df_display[['#', 'SEDE_NODAL', 'cantidad', 'porcentaje']]
            df_display.columns = ['#', 'Sede Nodal', 'Matriculados', 'Porcentaje']
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes matriculados**: {int(total_matriculados):,}
        - **Total sedes nodales**: {total_sedes}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())