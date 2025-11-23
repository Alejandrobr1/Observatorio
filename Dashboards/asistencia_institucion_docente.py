import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import text
import sys, os

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Base_datos.conexion import get_engine

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Docentes por Institución - Formación Docente")
st.title("📊 Docentes por Institución - FORMACIÓN DOCENTE")

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
    # Obtener años disponibles
    query_years = text("""
        SELECT DISTINCT pnm.ANIO_REGISTRO as año
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO IS NOT NULL
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion docente%'
        AND p.TIPO_PERSONA = 'Docente'
        AND pnm.ANIO_REGISTRO BETWEEN 2016 AND 2025
        ORDER BY año DESC
    """)
    result_years = connection.execute(query_years)
    available_years = [str(row[0]) for row in result_years.fetchall()]

    if not available_years:
        st.error("❌ No se encontraron datos de Formación Docente para docentes")
        st.stop()

    # Filtro de año
    selected_year = st.sidebar.selectbox(
        '📅 Año',
        available_years,
        index=0
    )

st.sidebar.divider()

# Información general
st.sidebar.header("📈 Estadísticas Generales")

with engine.connect() as connection:
    # Total docentes
    query_total = text("""
        SELECT COUNT(DISTINCT p.ID) as total 
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion docente%'
        AND p.TIPO_PERSONA = 'Docente'
    """)
    total_estudiantes = connection.execute(query_total, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Docentes ({selected_year})", f"{total_estudiantes:,}")
    
    # Total instituciones
    query_inst = text("""
        SELECT COUNT(DISTINCT i.ID) as total
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        INNER JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion docente%'
        AND p.TIPO_PERSONA = 'Docente'
        AND i.NOMBRE_INSTITUCION IS NOT NULL
        AND i.NOMBRE_INSTITUCION != ''
        AND i.NOMBRE_INSTITUCION != 'SIN INFORMACION'
    """)
    total_inst = connection.execute(query_inst, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Instituciones ({selected_year})", f"{total_inst:,}")

st.sidebar.divider()

# Consulta principal
try:
    with engine.connect() as connection:
        # Consulta para obtener docentes por institución - SOLO FORMACION DOCENTE Y DOCENTES
        query = text("""
            SELECT 
                i.NOMBRE_INSTITUCION,
                COUNT(DISTINCT p.ID) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
            WHERE pnm.ANIO_REGISTRO = :año
            AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion docente%'
            AND p.TIPO_PERSONA = 'Docente'
            AND i.NOMBRE_INSTITUCION IS NOT NULL
            AND i.NOMBRE_INSTITUCION != ''
            AND i.NOMBRE_INSTITUCION != 'SIN INFORMACION'
            GROUP BY i.NOMBRE_INSTITUCION
            ORDER BY cantidad DESC
        """)
        
        result = connection.execute(query, {"año": int(selected_year)})
        df = pd.DataFrame(result.fetchall(), columns=["INSTITUCION", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos de docentes para el año {selected_year}")
            st.stop()

        # Obtener lista de instituciones únicas ordenadas por total de docentes
        total_por_institucion = df.set_index('INSTITUCION')['cantidad'].sort_values(ascending=True)
        instituciones_ordenadas = total_por_institucion.index.tolist()
        
        # Top instituciones en sidebar
        st.sidebar.header(f"📊 Top 5 Instituciones - {selected_year}")
        top_5 = total_por_institucion.tail(5).sort_values(ascending=False)
        for idx, (inst, total) in enumerate(top_5.items(), 1):
            nombre_corto = inst[:30] + '...' if len(inst) > 30 else inst
            st.sidebar.write(f"**{idx}. {nombre_corto}**")
            st.sidebar.write(f"   {int(total):,} docentes")

        # Crear gráfico de barras horizontales
        st.header(f"📊 Distribución de Docentes por Institución - Formación Docente - Año {selected_year}")
        
        # Limitar a top 15 instituciones para mejor visualización
        num_instituciones_mostrar = min(15, len(instituciones_ordenadas))
        instituciones_mostrar = instituciones_ordenadas[-num_instituciones_mostrar:]
        valores_mostrar = [total_por_institucion[inst] for inst in instituciones_mostrar]
        
        fig, ax = plt.subplots(figsize=(14, max(10, num_instituciones_mostrar * 0.7)))
        
        y_pos = np.arange(len(instituciones_mostrar))
        
        # Crear barras horizontales con color gradual
        colors_gradient = plt.cm.viridis(np.linspace(0.3, 0.9, len(instituciones_mostrar)))
        
        bars = ax.barh(y_pos, valores_mostrar, color=colors_gradient,
                      edgecolor='black', linewidth=1.2)
        
        # Agregar etiquetas en las barras
        for i, (bar, valor) in enumerate(zip(bars, valores_mostrar)):
            ax.text(valor, i, f'  {int(valor):,}',
                   ha='left', va='center',
                   color='black', fontsize=10, fontweight='bold')
        
        # Preparar etiquetas de instituciones (acortar si son muy largas)
        labels_instituciones = []
        for inst in instituciones_mostrar:
            if len(inst) > 45:
                labels_instituciones.append(inst[:42] + '...')
            else:
                labels_instituciones.append(inst)
        
        # Configuración del gráfico
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels_instituciones, fontsize=10)
        ax.set_xlabel('Cantidad de Docentes', fontsize=13, fontweight='bold')
        ax.set_ylabel('Institución Educativa', fontsize=13, fontweight='bold')
        ax.set_title(f'Distribución de Docentes Formación Docente por Institución\nAño {selected_year}',
                    fontsize=16, fontweight='bold', pad=20)
        
        # Configurar límite del eje X
        max_val = max(valores_mostrar) if valores_mostrar else 1
        ax.set_xlim(0, max_val * 1.15)
        
        # Grid
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig)

        # Tabla resumen
        st.header("📋 Tabla Detallada por Institución")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📊 Todas las Instituciones - {selected_year}")
            
            # Crear tabla completa
            tabla_completa_final = []
            total_general = int(total_por_institucion.sum())
            for idx, institucion in enumerate(instituciones_ordenadas[::-1], 1):
                cantidad = total_por_institucion[institucion]
                porcentaje = (cantidad / total_general * 100) if total_general > 0 else 0
                
                tabla_completa_final.append({
                    '#': idx,
                    'Institución': institucion,
                    'Docentes': f"{int(cantidad):,}",
                    'Porcentaje': f"{porcentaje:.1f}%"
                })
            
            df_tabla = pd.DataFrame(tabla_completa_final)
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)
            
            st.info(f"**Total de docentes:** {int(total_general):,}")
        
        with col2:
            st.subheader("📊 Top 10")
            
            top_10 = total_por_institucion.tail(10).sort_values(ascending=False)
            
            fig_top, ax_top = plt.subplots(figsize=(7, 6))
            
            labels_top = [inst[:25] + '...' if len(inst) > 25 else inst for inst in top_10.index]
            colors_top = plt.cm.Set3(np.linspace(0, 1, len(top_10)))
            
            wedges, texts, autotexts = ax_top.pie(
                top_10.values,
                labels=labels_top,
                autopct='%1.1f%%',
                colors=colors_top,
                startangle=90,
                textprops={'fontsize': 8, 'fontweight': 'bold'}
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(8)
            
            ax_top.set_title('Top 10 Instituciones\nFormación Docente', 
                            fontsize=12, fontweight='bold', pad=15)
            
            st.pyplot(fig_top)

        # Estadísticas adicionales
        st.header("📈 Estadísticas Resumen")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Docentes", f"{int(total_general):,}")
        
        with col2:
            st.metric("Total Instituciones", f"{len(instituciones_ordenadas):,}")
        
        with col3:
            promedio = total_general / len(instituciones_ordenadas) if instituciones_ordenadas else 0
            st.metric("Promedio por Institución", f"{int(promedio):,}")
        
        with col4:
            max_inst = total_por_institucion.idxmax()
            max_val = total_por_institucion.max()
            st.metric("Institución Mayor", f"{int(max_val):,}")

        with st.expander("🔍 Ver datos detallados"):
            st.dataframe(df.sort_values('cantidad', ascending=False), use_container_width=True, hide_index=True)
        
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Curso**: Formación Docente
        - **Tipo de población**: Docente
        - **Año**: {selected_year}
        - **Total docentes**: {int(total_general):,}
        - **Total instituciones**: {len(instituciones_ordenadas)}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
