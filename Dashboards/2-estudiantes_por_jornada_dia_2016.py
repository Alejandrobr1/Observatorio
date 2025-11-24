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
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Jornada y Día")
st.title("📊 Estudiantes Matriculados por Jornada y Día")

# Inicializar conexión
try:
    engine = get_engine()
    st.sidebar.success("✅ Conexión establecida")
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
    
    # Total jornadas
    query_jornadas = text(f"SELECT COUNT(DISTINCT JORNADA) FROM {table_name} WHERE JORNADA IS NOT NULL AND JORNADA != '' AND JORNADA != 'SIN INFORMACION'")
    total_jornadas = connection.execute(query_jornadas).scalar() or 0
    st.sidebar.metric(f"Total Jornadas ({selected_year})", f"{total_jornadas:,}")
    
    # Total días
    query_dias = text(f"SELECT COUNT(DISTINCT DIA) FROM {table_name} WHERE DIA IS NOT NULL AND DIA != '' AND DIA != 'SIN INFORMACION'")
    total_dias = connection.execute(query_dias).scalar() or 0
    st.sidebar.metric(f"Total Días ({selected_year})", f"{total_dias:,}")

st.sidebar.divider()

# Consulta principal
try:
    with engine.connect() as connection:
        table_name = f"Estudiantes_{selected_year}"
        
        # Consulta para obtener matriculados por día y jornada
        query = text(f"""
            SELECT 
                DIA,
                JORNADA,
                COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE DIA IS NOT NULL AND DIA != '' AND DIA != 'SIN INFORMACION'
              AND JORNADA IS NOT NULL AND JORNADA != '' AND JORNADA != 'SIN INFORMACION'
            GROUP BY DIA, JORNADA
            ORDER BY DIA, JORNADA
        """)
        
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["DIA", "JORNADA", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos de matriculados por jornada y día para el año {selected_year}.")
            st.stop()

        # Pivotear los datos para tener días como índice y jornadas como columnas
        df_pivot = df.pivot(index='DIA', columns='JORNADA', values='cantidad').fillna(0)

        # Crear gráfico de barras verticales agrupadas
        st.header(f"📊 Matriculados por Jornada y Día - Año {selected_year}")
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        dias = df_pivot.index
        jornadas = df_pivot.columns
        n_dias = len(dias)
        n_jornadas = len(jornadas)
        
        x = np.arange(n_dias)  # Posiciones de los grupos de barras (días)
        width = 0.8 / n_jornadas  # Ancho de cada barra
        
        # Colores para cada jornada
        colors = plt.cm.viridis(np.linspace(0, 1, n_jornadas))
        
        # Crear las barras para cada jornada
        for i, jornada in enumerate(jornadas):
            offset = width * (i - (n_jornadas - 1) / 2)
            valores = df_pivot[jornada]
            bars = ax.bar(x + offset, valores, width, label=jornada, color=colors[i], edgecolor='black', linewidth=1)
            
            # Añadir etiquetas de valor sobre cada barra
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{int(height):,}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Configuración del gráfico
        ax.set_xlabel('Día de la Semana', fontsize=13, fontweight='bold')
        ax.set_ylabel('Cantidad de Estudiantes Matriculados', fontsize=13, fontweight='bold')
        ax.set_title(f'Estudiantes Matriculados por Jornada y Día\nAño {selected_year}',
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(dias, rotation=45, ha='right', fontsize=11)
        ax.legend(title='Jornada', fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Ajustar el límite del eje Y para dar espacio a las etiquetas
        max_val = df_pivot.sum(axis=1).max()
        ax.set_ylim(0, float(max_val) * 1.2)
        
        plt.tight_layout()
        st.pyplot(fig)

        # Tabla de datos detallada
        st.header("📋 Tabla Detallada")
        
        # Formatear el DataFrame pivoteado para mostrarlo
        df_display = df_pivot.copy()
        df_display = df_display.astype(int).applymap('{:,}'.format)
        df_display['Total por Día'] = df_pivot.sum(axis=1).astype(int).apply('{:,}'.format)
        
        st.dataframe(df_display, use_container_width=True)
        
        # Información adicional
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes matriculados**: {int(total_matriculados):,}
        - **Total jornadas**: {total_jornadas}
        - **Total días**: {total_dias}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
