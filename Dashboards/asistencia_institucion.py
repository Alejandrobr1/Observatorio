import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Institución")
st.title("🏫 Distribución de Estudiantes por Institución Educativa")

# Configuración de la conexión a la base de datos
@st.cache_resource
def get_database_connection():
    try:
        engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"Error al conectar a la base de datos: {str(e)}")
        raise e

# Inicializar conexión
try:
    engine = get_database_connection()
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
        WHERE pnm.ANIO_REGISTRO IS NOT NULL
        ORDER BY año DESC
    """)
    result_years = connection.execute(query_years)
    available_years = [str(row[0]) for row in result_years.fetchall()]

    if not available_years:
        st.error("No se encontraron años en la base de datos")
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
    # Total estudiantes en el año seleccionado
    query_total_year = text("""
        SELECT COUNT(DISTINCT p.ID) as total 
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND p.TIPO_PERSONA = 'Estudiante'
    """)
    total_year = connection.execute(query_total_year, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{total_year:,}")
    
    # Total instituciones
    query_total_inst = text("""
        SELECT COUNT(DISTINCT i.ID) as total
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        INNER JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND p.TIPO_PERSONA = 'Estudiante'
        AND i.NOMBRE_INSTITUCION IS NOT NULL
        AND i.NOMBRE_INSTITUCION != ''
    """)
    total_inst = connection.execute(query_total_inst, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Instituciones ({selected_year})", f"{total_inst:,}")

st.sidebar.divider()

# Consulta principal para obtener estudiantes por institución
try:
    with engine.connect() as connection:
        # Consulta para obtener cantidad de estudiantes por institución
        query = text("""
            SELECT 
                i.NOMBRE_INSTITUCION,
                COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
            WHERE pnm.ANIO_REGISTRO = :año
            AND p.TIPO_PERSONA = 'Estudiante'
            AND i.NOMBRE_INSTITUCION IS NOT NULL
            AND i.NOMBRE_INSTITUCION != ''
            AND i.NOMBRE_INSTITUCION != 'SIN INFORMACION'
            GROUP BY i.NOMBRE_INSTITUCION
            ORDER BY cantidad DESC
        """)
        
        result = connection.execute(query, {"año": int(selected_year)})
        df = pd.DataFrame(result.fetchall(), columns=["INSTITUCION", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos de instituciones para el año {selected_year}")
            st.stop()

        total_estudiantes = df['cantidad'].sum()
        
        # Calcular porcentajes
        df['porcentaje'] = (df['cantidad'] / total_estudiantes * 100).round(1)
        
        # Mostrar top 5 en sidebar
        st.sidebar.header(f"📊 Top 5 Instituciones - {selected_year}")
        for idx, row in df.head(5).iterrows():
            institucion = row['INSTITUCION']
            cantidad = int(row['cantidad'])
            porcentaje = row['porcentaje']
            # Acortar nombre si es muy largo
            nombre_corto = institucion[:25] + '...' if len(institucion) > 25 else institucion
            st.sidebar.write(f"**{idx+1}. {nombre_corto}**")
            st.sidebar.write(f"   {cantidad:,} ({porcentaje}%)")

        # Crear gráfico de pastel principal
        st.header(f"📊 Distribución de Estudiantes por Institución - Año {selected_year}")
        
        # Limitar a top 10 para mejor visualización
        num_instituciones_mostrar = min(10, len(df))
        df_top = df.head(num_instituciones_mostrar).copy()
        
        # Si hay más de 10, agrupar el resto como "Otras"
        if len(df) > num_instituciones_mostrar:
            otras_cantidad = df.iloc[num_instituciones_mostrar:]['cantidad'].sum()
            df_otras = pd.DataFrame([{'INSTITUCION': 'Otras Instituciones', 'cantidad': otras_cantidad, 
                                      'porcentaje': (otras_cantidad / total_estudiantes * 100).round(1)}])
            df_top = pd.concat([df_top, df_otras], ignore_index=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Generar colores automáticamente
            num_colores = len(df_top)
            colors = plt.cm.Set3(np.linspace(0, 1, num_colores))
            
            # Crear explode dinámicamente
            explode = tuple([0.02] * num_colores)
            
            # Preparar etiquetas más cortas para el gráfico
            labels_cortos = []
            for inst in df_top['INSTITUCION']:
                if len(inst) > 30:
                    labels_cortos.append(inst[:27] + '...')
                else:
                    labels_cortos.append(inst)
            
            # Crear el gráfico de pastel
            wedges, texts, autotexts = ax.pie(
                df_top['cantidad'], 
                labels=labels_cortos,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                explode=explode,
                textprops={'fontsize': 10},
                shadow=True,
                pctdistance=0.85
            )
            
            # Mejorar el formato de los textos
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
            
            for text in texts:
                text.set_fontsize(10)
                text.set_fontweight('bold')
            
            ax.set_title(f'Distribución de Estudiantes por Institución\nAño {selected_year}', 
                        fontsize=16, fontweight='bold', pad=20)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.subheader("📋 Resumen")
            
            # Mostrar solo top 10 en la tabla
            st.write(f"**Top {len(df_top)} Instituciones:**")
            
            tabla_resumen = []
            for idx, row in df_top.iterrows():
                institucion = row['INSTITUCION']
                cantidad = int(row['cantidad'])
                porcentaje = row['porcentaje']
                
                # Acortar nombre para la tabla
                nombre_tabla = institucion[:35] + '...' if len(institucion) > 35 else institucion
                
                tabla_resumen.append({
                    '#': idx + 1,
                    'Institución': nombre_tabla,
                    'Estudiantes': f"{cantidad:,}",
                    '%': f"{porcentaje}%"
                })
            
            df_resumen = pd.DataFrame(tabla_resumen)
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
            
            # Totales
            st.divider()
            st.metric("**Total Estudiantes**", f"{int(total_estudiantes):,}")
            st.metric("**Total Instituciones**", f"{len(df):,}")

        # Gráfico de barras para top 10
        st.header("📊 Top 10 Instituciones - Vista de Barras")
        
        df_top_10 = df.head(10)
        
        fig_bar, ax_bar = plt.subplots(figsize=(12, 8))
        
        # Acortar nombres para el eje Y
        labels_bar = []
        for inst in df_top_10['INSTITUCION']:
            if len(inst) > 40:
                labels_bar.append(inst[:37] + '...')
            else:
                labels_bar.append(inst)
        
        y_pos = np.arange(len(df_top_10))
        
        bars = ax_bar.barh(
            y_pos,
            df_top_10['cantidad'],
            color=plt.cm.Set3(np.linspace(0, 1, len(df_top_10))),
            edgecolor='black',
            linewidth=1.5
        )
        
        # Agregar valores en las barras
        for i, (bar, cantidad) in enumerate(zip(bars, df_top_10['cantidad'])):
            width = bar.get_width()
            ax_bar.text(
                width, 
                bar.get_y() + bar.get_height()/2.,
                f' {int(cantidad):,}',
                ha='left', 
                va='center',
                fontsize=10,
                fontweight='bold'
            )
        
        ax_bar.set_yticks(y_pos)
        ax_bar.set_yticklabels(labels_bar, fontsize=10)
        ax_bar.set_xlabel('Cantidad de Estudiantes', fontsize=12, fontweight='bold')
        ax_bar.set_title(f'Top 10 Instituciones con Más Estudiantes - Año {selected_year}', 
                        fontsize=14, fontweight='bold', pad=15)
        ax_bar.grid(axis='x', alpha=0.3, linestyle='--')
        ax_bar.invert_yaxis()  # La institución con más estudiantes arriba
        
        plt.tight_layout()
        st.pyplot(fig_bar)

        # Tabla completa (expandible)
        with st.expander("🔍 Ver listado completo de todas las instituciones"):
            st.write(f"**Total: {len(df)} instituciones**")
            
            df_completo = df.copy()
            df_completo['#'] = range(1, len(df_completo) + 1)
            df_completo = df_completo[['#', 'INSTITUCION', 'cantidad', 'porcentaje']]
            df_completo.columns = ['#', 'Institución', 'Estudiantes', 'Porcentaje (%)']
            
            st.dataframe(df_completo, use_container_width=True, hide_index=True)

        # Estadísticas adicionales
        st.header("📈 Estadísticas Adicionales")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            promedio = df['cantidad'].mean()
            st.metric("Promedio por Institución", f"{int(promedio):,}")
        
        with col_stat2:
            mediana = df['cantidad'].median()
            st.metric("Mediana", f"{int(mediana):,}")
        
        with col_stat3:
            max_estudiantes = df['cantidad'].max()
            st.metric("Institución Más Grande", f"{int(max_estudiantes):,}")
        
        with col_stat4:
            min_estudiantes = df['cantidad'].min()
            st.metric("Institución Más Pequeña", f"{int(min_estudiantes):,}")
        
        # Información adicional
        institucion_mayor = df.iloc[0]['INSTITUCION']
        
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes**: {int(total_estudiantes):,}
        - **Total instituciones**: {len(df):,}
        - **Institución con más estudiantes**: {institucion_mayor} ({int(df.iloc[0]['cantidad']):,} estudiantes)
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        import traceback
        st.code(traceback.format_exc())
