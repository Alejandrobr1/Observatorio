import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine, text

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Aprobación de Estudiantes")
st.title("📊 Aprobación de Estudiantes por Año")

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
        SELECT COUNT(DISTINCT pnm.PERSONA_ID) as total 
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND p.TIPO_PERSONA = 'Estudiante'
    """)
    total_year = connection.execute(query_total_year, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{total_year:,}")

st.sidebar.divider()

# Consulta principal para obtener aprobación
try:
    with engine.connect() as connection:
        # Consulta para obtener estado de aprobación
        query = text("""
            SELECT 
                n.ESTADO_ESTUDIANTE,
                COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
            WHERE pnm.ANIO_REGISTRO = :año
            AND p.TIPO_PERSONA = 'Estudiante'
            AND n.ESTADO_ESTUDIANTE IS NOT NULL
            AND n.ESTADO_ESTUDIANTE != ''
            AND n.ESTADO_ESTUDIANTE != 'SIN INFORMACION'
            GROUP BY n.ESTADO_ESTUDIANTE
            ORDER BY n.ESTADO_ESTUDIANTE
        """)
        
        result = connection.execute(query, {"año": int(selected_year)})
        df = pd.DataFrame(result.fetchall(), columns=["ESTADO_ESTUDIANTE", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos de aprobación para el año {selected_year}")
            
            # Mostrar diagnóstico
            with st.expander("🔍 Diagnóstico"):
                query_estados = text("""
                    SELECT DISTINCT n.ESTADO_ESTUDIANTE, COUNT(*) as cantidad
                    FROM Persona_Nivel_MCER pnm
                    INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
                    WHERE pnm.ANIO_REGISTRO = :año
                    GROUP BY n.ESTADO_ESTUDIANTE
                """)
                result_estados = connection.execute(query_estados, {"año": int(selected_year)})
                st.write("**Estados disponibles en la BD:**")
                for row in result_estados:
                    st.write(f"- '{row[0]}': {row[1]} registros")
            
            st.stop()

        # Normalizar los nombres de estados
        df['ESTADO_NORMALIZADO'] = df['ESTADO_ESTUDIANTE'].str.upper().str.strip()
        
        # Categorizar en Aprobó / No Aprobó
        def categorizar_estado(estado):
            if pd.isna(estado):
                return 'Sin Información'
            estado_upper = str(estado).upper().strip()
            
            if any(keyword in estado_upper for keyword in ['APROB', 'APROBO', 'APROBADO', 'PASSED', 'PASS']):
                return 'Aprobó'
            elif any(keyword in estado_upper for keyword in ['NO APROB', 'REPROB', 'REPROBADO', 'FAILED', 'FAIL']):
                return 'No Aprobó'
            else:
                return 'Otro'
        
        df['CATEGORIA'] = df['ESTADO_NORMALIZADO'].apply(categorizar_estado)
        
        # Agrupar por categoría
        df_agrupado = df.groupby('CATEGORIA')['cantidad'].sum().reset_index()
        
        # Filtrar categorías válidas
        df_final = df_agrupado[df_agrupado['CATEGORIA'].isin(['Aprobó', 'No Aprobó'])]
        
        if df_final.empty:
            st.warning(f"⚠️ No se encontraron registros de Aprobó/No Aprobó para el año {selected_year}")
            st.info("Los estados disponibles son:")
            st.dataframe(df[['ESTADO_ESTUDIANTE', 'cantidad']])
            st.stop()

        total_estudiantes = df_final['cantidad'].sum()
        
        # Mostrar estadísticas en sidebar
        st.sidebar.header(f"📊 Aprobación - {selected_year}")
        for _, row in df_final.iterrows():
            categoria = row['CATEGORIA']
            cantidad = int(row['cantidad'])
            porcentaje = (cantidad / total_estudiantes * 100) if total_estudiantes > 0 else 0
            st.sidebar.metric(categoria, f"{cantidad:,}", f"{porcentaje:.1f}%")

        # Crear gráfico de pastel principal
        st.header(f"📊 Distribución de Aprobación - Año {selected_year}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Colores personalizados (adaptables al número de categorías)
            colors_map = {
                'Aprobó': '#27ae60',
                'No Aprobó': '#e74c3c'
            }
            colors = [colors_map.get(cat, '#95a5a6') for cat in df_final['CATEGORIA']]
            
            # CORRECCIÓN: Crear explode dinámicamente según el número de categorías
            num_categorias = len(df_final)
            explode = tuple([0.05] * num_categorias)  # Un valor 0.05 por cada categoría
            
            # Crear el gráfico de pastel
            wedges, texts, autotexts = ax.pie(
                df_final['cantidad'], 
                labels=df_final['CATEGORIA'],
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                explode=explode,
                textprops={'fontsize': 14, 'fontweight': 'bold'},
                shadow=True
            )
            
            # Mejorar el formato de los textos
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(16)
                autotext.set_fontweight('bold')
            
            for text in texts:
                text.set_fontsize(16)
                text.set_fontweight('bold')
            
            ax.set_title(f'Aprobación de Estudiantes\nAño {selected_year}', 
                        fontsize=18, fontweight='bold', pad=20)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.subheader("📋 Resumen")
            
            # Tabla de resumen
            tabla_resumen = []
            for _, row in df_final.iterrows():
                categoria = row['CATEGORIA']
                cantidad = int(row['cantidad'])
                porcentaje = (cantidad / total_estudiantes * 100) if total_estudiantes > 0 else 0
                
                tabla_resumen.append({
                    'Estado': categoria,
                    'Cantidad': f"{cantidad:,}",
                    'Porcentaje': f"{porcentaje:.1f}%"
                })
            
            df_resumen = pd.DataFrame(tabla_resumen)
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
            
            # Totales
            st.divider()
            st.metric("**Total Estudiantes**", f"{int(total_estudiantes):,}")
            
            # Tasa de aprobación
            aprobo_row = df_final[df_final['CATEGORIA'] == 'Aprobó']
            aprobo = aprobo_row['cantidad'].sum() if not aprobo_row.empty else 0
            tasa_aprobacion = (aprobo / total_estudiantes * 100) if total_estudiantes > 0 else 0
            
            if tasa_aprobacion >= 70:
                st.success(f"✅ Tasa de Aprobación: **{tasa_aprobacion:.1f}%**")
            elif tasa_aprobacion >= 50:
                st.warning(f"⚠️ Tasa de Aprobación: **{tasa_aprobacion:.1f}%**")
            else:
                st.error(f"❌ Tasa de Aprobación: **{tasa_aprobacion:.1f}%**")

        # Gráfico de barras adicional
        st.header("📊 Comparación Visual")
        
        fig_bar, ax_bar = plt.subplots(figsize=(10, 6))
        
        bars = ax_bar.bar(
            df_final['CATEGORIA'], 
            df_final['cantidad'],
            color=colors,
            edgecolor='black',
            linewidth=2
        )
        
        # Agregar valores en las barras
        for bar in bars:
            height = bar.get_height()
            ax_bar.text(
                bar.get_x() + bar.get_width()/2., 
                height,
                f'{int(height):,}',
                ha='center', 
                va='bottom',
                fontsize=14,
                fontweight='bold'
            )
        
        ax_bar.set_xlabel('Estado', fontsize=14, fontweight='bold')
        ax_bar.set_ylabel('Cantidad de Estudiantes', fontsize=14, fontweight='bold')
        ax_bar.set_title(f'Cantidad de Estudiantes por Estado - Año {selected_year}', 
                        fontsize=16, fontweight='bold', pad=20)
        ax_bar.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig_bar)

        # Datos detallados (expandible)
        with st.expander("🔍 Ver datos completos por estado"):
            st.write("**Estados originales en la base de datos:**")
            st.dataframe(df[['ESTADO_ESTUDIANTE', 'cantidad']].sort_values('cantidad', ascending=False), 
                        use_container_width=True, hide_index=True)
        
        # Información adicional
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes evaluados**: {int(total_estudiantes):,}
        - **Aprobados**: {int(aprobo):,}
        - **No aprobados**: {int(total_estudiantes - aprobo):,}
        - **Tasa de aprobación**: {tasa_aprobacion:.1f}%
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        import traceback
        st.code(traceback.format_exc())
