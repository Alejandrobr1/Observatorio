import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import traceback
from sqlalchemy import text, create_engine
import sys 
import os
import numpy as np

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Sede Nodal")
st.title("📊 Estudiantes Matriculados por Sede Nodal")

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
        help="Selecciona el año para visualizar los datos de matriculados."
    )

st.sidebar.divider()

# Información general
st.sidebar.header("📈 Estadísticas Generales")

# Consulta principal
try:
    with engine.connect() as connection:
        # Construir el nombre de la tabla dinámicamente
        table_name = f"Estudiantes_{selected_year}"
        
        # Consulta para obtener estudiantes matriculados por sede nodal
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

        # Convertir a numérico para evitar errores de tipo
        df['cantidad'] = pd.to_numeric(df['cantidad'])

        # Actualizar métricas del sidebar con los datos cargados
        total_matriculados = df['cantidad'].sum()
        total_sedes = len(df)
        st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
        st.sidebar.metric(f"Total Sedes Nodales ({selected_year})", f"{total_sedes:,}")
        st.sidebar.divider()
        
        # Top 5 sedes en sidebar
        st.sidebar.header(f"📊 Top 5 Sedes Nodales - {selected_year}")
        top_5 = df.head(5)
        for idx, row in top_5.iterrows():
            nombre_sede = row['SEDE_NODAL']
            total = row['cantidad']
            nombre_corto = nombre_sede[:30] + '...' if len(nombre_sede) > 30 else nombre_sede
            st.sidebar.write(f"**{idx+1}. {nombre_corto}**")
            st.sidebar.write(f"   {int(total):,} matriculados")

        # Crear gráfico de barras horizontales
        st.header(f"📊 Matriculados por Sede Nodal - Año {selected_year}")
        
        # Usar todos los datos, ordenados de mayor a menor
        df_sorted = df.sort_values('cantidad', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(df_sorted) * 0.5)))
        
        y_pos = range(len(df_sorted))
        
        # Crear barras horizontales con color gradual
        colors_gradient = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_sorted)))
        
        bars = ax.barh(y_pos, df_sorted['cantidad'], color=colors_gradient,
                      edgecolor='black', linewidth=1.2)
        
        # Agregar etiquetas en las barras
        for i, (bar, valor) in enumerate(zip(bars, df_sorted['cantidad'])):
            ax.text(valor, i, f'  {int(valor):,}',
                   ha='left', va='center',
                   color='black', fontsize=10, fontweight='bold')
        
        # Configuración del gráfico
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_sorted['SEDE_NODAL'], fontsize=10)
        ax.set_xlabel('Cantidad de Estudiantes Matriculados', fontsize=13, fontweight='bold')
        ax.set_ylabel('Sede Nodal', fontsize=13, fontweight='bold')
        ax.set_title(f'Estudiantes Matriculados por Sede Nodal\nAño {selected_year}',
                    fontsize=16, fontweight='bold', pad=20)
        
        # Configurar límite del eje X
        max_val = df_sorted['cantidad'].max() if not df_sorted.empty else 1
        ax.set_xlim(0, float(max_val) * 1.15)
        
        # Grid
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig)

        # Tabla resumen
        st.header("📋 Tabla Detallada por Sede Nodal")
        
        # Calcular porcentajes
        df['porcentaje'] = (df['cantidad'] / float(total_matriculados) * 100) if total_matriculados > 0 else 0
        
        # Formatear para visualización
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
