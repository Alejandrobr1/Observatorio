import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Sexo y Grado")
st.title("📊 Distribución de Estudiantes por Sexo y Grado")

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
    # Total estudiantes
    query_total = text("""
        SELECT COUNT(DISTINCT p.ID) as total 
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND p.TIPO_PERSONA = 'Estudiante'
    """)
    total_estudiantes = connection.execute(query_total, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{total_estudiantes:,}")
    
    # Total por sexo
    query_sexo = text("""
        SELECT 
            p.SEXO,
            COUNT(DISTINCT p.ID) as cantidad
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND p.TIPO_PERSONA = 'Estudiante'
        AND p.SEXO IS NOT NULL
        AND p.SEXO != ''
        AND p.SEXO != 'SIN INFORMACION'
        GROUP BY p.SEXO
    """)
    result_sexo = connection.execute(query_sexo, {"año": int(selected_year)})
    
    st.sidebar.write("**Por Sexo:**")
    for row in result_sexo:
        sexo = row[0]
        cantidad = row[1]
        porcentaje = (cantidad / total_estudiantes * 100) if total_estudiantes > 0 else 0
        st.sidebar.write(f"• {sexo}: {cantidad:,} ({porcentaje:.1f}%)")

st.sidebar.divider()

# Consulta principal para obtener estudiantes por sexo y grado
try:
    with engine.connect() as connection:
        # Consulta para obtener datos por grado y sexo
        query = text("""
            SELECT 
                n.GRADO,
                p.SEXO,
                COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
            WHERE pnm.ANIO_REGISTRO = :año
            AND p.TIPO_PERSONA = 'Estudiante'
            AND n.GRADO IS NOT NULL
            AND n.GRADO != ''
            AND n.GRADO != 'SIN INFORMACION'
            AND p.SEXO IS NOT NULL
            AND p.SEXO != ''
            AND p.SEXO != 'SIN INFORMACION'
            GROUP BY n.GRADO, p.SEXO
            ORDER BY n.GRADO, p.SEXO
        """)
        
        result = connection.execute(query, {"año": int(selected_year)})
        df = pd.DataFrame(result.fetchall(), columns=["GRADO", "SEXO", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos de grados para el año {selected_year}")
            
            # Diagnóstico
            with st.expander("🔍 Diagnóstico"):
                query_grados = text("""
                    SELECT DISTINCT n.GRADO, COUNT(*) as cantidad
                    FROM Persona_Nivel_MCER pnm
                    INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
                    WHERE pnm.ANIO_REGISTRO = :año
                    GROUP BY n.GRADO
                """)
                result_grados = connection.execute(query_grados, {"año": int(selected_year)})
                st.write("**Grados disponibles en la BD:**")
                for row in result_grados:
                    st.write(f"- '{row[0]}': {row[1]} registros")
            
            st.stop()

        # Normalizar sexo
        df['SEXO_NORMALIZADO'] = df['SEXO'].str.upper().str.strip()
        
        # Categorizar sexo
        def categorizar_sexo(sexo):
            if pd.isna(sexo):
                return 'Otro'
            sexo_upper = str(sexo).upper()
            if any(keyword in sexo_upper for keyword in ['M', 'MASCULINO', 'HOMBRE', 'MALE']):
                return 'Masculino'
            elif any(keyword in sexo_upper for keyword in ['F', 'FEMENINO', 'MUJER', 'FEMALE']):
                return 'Femenino'
            else:
                return 'Otro'
        
        df['SEXO_CATEGORIA'] = df['SEXO_NORMALIZADO'].apply(categorizar_sexo)
        
        # Agrupar por grado y sexo categorizado
        df_agrupado = df.groupby(['GRADO', 'SEXO_CATEGORIA'])['cantidad'].sum().reset_index()
        
        # Obtener lista única de grados
        grados_unicos = sorted(df_agrupado['GRADO'].unique())
        
        # Preparar datos para el gráfico
        masculino_por_grado = []
        femenino_por_grado = []
        
        for grado in grados_unicos:
            # Masculino
            masc = df_agrupado[(df_agrupado['GRADO'] == grado) & (df_agrupado['SEXO_CATEGORIA'] == 'Masculino')]
            masculino_por_grado.append(masc['cantidad'].sum() if not masc.empty else 0)
            
            # Femenino
            fem = df_agrupado[(df_agrupado['GRADO'] == grado) & (df_agrupado['SEXO_CATEGORIA'] == 'Femenino')]
            femenino_por_grado.append(fem['cantidad'].sum() if not fem.empty else 0)
        
        total_por_grado = [m + f for m, f in zip(masculino_por_grado, femenino_por_grado)]
        
        # Mostrar estadísticas en sidebar
        st.sidebar.header(f"📊 Por Grado - {selected_year}")
        st.sidebar.write(f"**Total de grados:** {len(grados_unicos)}")

        # MODIFICADO: Crear gráfico de barras horizontales apiladas (izquierda a derecha)
        st.header(f"📊 Distribución por Sexo y Grado - Año {selected_year}")
        
        fig, ax = plt.subplots(figsize=(14, max(8, len(grados_unicos) * 0.6)))
        
        y_pos = np.arange(len(grados_unicos))
        
        # NUEVO: Barras apiladas horizontalmente
        # Masculino primero (desde 0)
        bars_masc = ax.barh(y_pos, masculino_por_grado, height=0.7,
                           label='Masculino', color='#3498db', 
                           edgecolor='black', linewidth=1.5)
        
        # Femenino apilado sobre masculino (comienza donde termina masculino)
        bars_fem = ax.barh(y_pos, femenino_por_grado, height=0.7,
                          left=masculino_por_grado,  # Comienza donde termina masculino
                          label='Femenino', color='#e74c3c',
                          edgecolor='black', linewidth=1.5)
        
        # Agregar valores en las barras
        for i, (masc, fem, total) in enumerate(zip(masculino_por_grado, femenino_por_grado, total_por_grado)):
            # Valor masculino (centro de la barra masculina)
            if masc > 0:
                ax.text(masc/2, i, f'{int(masc):,}', 
                       ha='center', va='center',
                       color='white', fontsize=10, fontweight='bold')
            
            # Valor femenino (centro de la barra femenina)
            if fem > 0:
                ax.text(masc + fem/2, i, f'{int(fem):,}',
                       ha='center', va='center',
                       color='white', fontsize=10, fontweight='bold')
            
            # Total al final de la barra
            if total > 0:
                ax.text(total, i, f'  {int(total):,}',
                       ha='left', va='center',
                       color='black', fontsize=10, fontweight='bold')
        
        # Configuración del gráfico
        ax.set_yticks(y_pos)
        ax.set_yticklabels(grados_unicos, fontsize=11)
        ax.set_xlabel('Cantidad de Estudiantes', fontsize=13, fontweight='bold')
        ax.set_ylabel('Grado', fontsize=13, fontweight='bold')
        ax.set_title(f'Distribución de Estudiantes por Sexo y Grado\nAño {selected_year}',
                    fontsize=16, fontweight='bold', pad=20)
        
        # Configurar el límite del eje X
        max_val = max(total_por_grado)
        ax.set_xlim(0, max_val * 1.15)
        
        # Leyenda
        ax.legend(loc='upper right', fontsize=12, framealpha=0.9)
        
        # Grid
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig)

        # Tabla resumen
        st.header("📋 Tabla Resumen por Grado")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Crear tabla de datos
            tabla_data = []
            for i, grado in enumerate(grados_unicos):
                masc = masculino_por_grado[i]
                fem = femenino_por_grado[i]
                total = masc + fem
                
                tabla_data.append({
                    'Grado': grado,
                    'Masculino': f"{int(masc):,}",
                    'Femenino': f"{int(fem):,}",
                    'Total': f"{int(total):,}",
                    '% Masculino': f"{(masc/total*100):.1f}%" if total > 0 else "0%",
                    '% Femenino': f"{(fem/total*100):.1f}%" if total > 0 else "0%"
                })
            
            # Agregar fila de totales
            total_masc = sum(masculino_por_grado)
            total_fem = sum(femenino_por_grado)
            total_general = total_masc + total_fem
            
            tabla_data.append({
                'Grado': 'TOTAL',
                'Masculino': f"{int(total_masc):,}",
                'Femenino': f"{int(total_fem):,}",
                'Total': f"{int(total_general):,}",
                '% Masculino': f"{(total_masc/total_general*100):.1f}%" if total_general > 0 else "0%",
                '% Femenino': f"{(total_fem/total_general*100):.1f}%" if total_general > 0 else "0%"
            })
            
            df_tabla = pd.DataFrame(tabla_data)
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 Totales Generales")
            
            st.metric("Total Estudiantes", f"{int(total_general):,}")
            st.metric("Total Masculino", f"{int(total_masc):,}", 
                     f"{(total_masc/total_general*100):.1f}%" if total_general > 0 else "0%")
            st.metric("Total Femenino", f"{int(total_fem):,}",
                     f"{(total_fem/total_general*100):.1f}%" if total_general > 0 else "0%")
            
            # Gráfico de pastel de distribución total
            st.subheader("Distribución Total por Sexo")
            
            fig_pie, ax_pie = plt.subplots(figsize=(6, 6))
            
            colors_pie = ['#3498db', '#e74c3c']
            explode_pie = (0.05, 0.05)
            
            ax_pie.pie([total_masc, total_fem],
                      labels=['Masculino', 'Femenino'],
                      autopct='%1.1f%%',
                      colors=colors_pie,
                      explode=explode_pie,
                      startangle=90,
                      textprops={'fontsize': 11, 'fontweight': 'bold'},
                      shadow=True)
            
            ax_pie.set_title('Distribución por Sexo', fontsize=12, fontweight='bold', pad=15)
            st.pyplot(fig_pie)

        # Gráfico de barras verticales apiladas
        st.header("📊 Vista Alternativa - Barras Verticales Apiladas")
        
        fig_stack, ax_stack = plt.subplots(figsize=(14, 8))
        
        x_pos = np.arange(len(grados_unicos))
        width = 0.7
        
        bars1 = ax_stack.bar(x_pos, masculino_por_grado, width, 
                            label='Masculino', color='#3498db',
                            edgecolor='black', linewidth=1.5)
        
        bars2 = ax_stack.bar(x_pos, femenino_por_grado, width, 
                            bottom=masculino_por_grado,
                            label='Femenino', color='#e74c3c',
                            edgecolor='black', linewidth=1.5)
        
        # Agregar totales encima de las barras
        for i, total in enumerate(total_por_grado):
            ax_stack.text(i, total, f'{int(total):,}',
                         ha='center', va='bottom',
                         fontsize=10, fontweight='bold')
        
        ax_stack.set_xlabel('Grado', fontsize=13, fontweight='bold')
        ax_stack.set_ylabel('Cantidad de Estudiantes', fontsize=13, fontweight='bold')
        ax_stack.set_title(f'Distribución de Estudiantes por Grado (Apilado Vertical)\nAño {selected_year}',
                          fontsize=16, fontweight='bold', pad=20)
        ax_stack.set_xticks(x_pos)
        ax_stack.set_xticklabels(grados_unicos, rotation=45, ha='right')
        ax_stack.legend(loc='upper right', fontsize=12)
        ax_stack.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig_stack)

        # Datos detallados
        with st.expander("🔍 Ver datos completos por grado y sexo"):
            st.dataframe(df_agrupado.sort_values(['GRADO', 'SEXO_CATEGORIA']), 
                        use_container_width=True, hide_index=True)
        
        # Información adicional
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Total estudiantes**: {int(total_general):,}
        - **Total grados**: {len(grados_unicos)}
        - **Masculino**: {int(total_masc):,} ({(total_masc/total_general*100):.1f}%)
        - **Femenino**: {int(total_fem):,} ({(total_fem/total_general*100):.1f}%)
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        import traceback
        st.code(traceback.format_exc())
