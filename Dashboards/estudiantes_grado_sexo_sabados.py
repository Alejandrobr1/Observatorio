import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import create_engine, text

st.set_page_config(layout="wide", page_title="Dashboard Estudiantes por Sexo y Grado - Formación Sábados")
st.title("📊 Distribución de Estudiantes por Sexo y Grado - FORMACIÓN SÁBADOS")

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

try:
    engine = get_database_connection()
    st.sidebar.success("✅ Conexión establecida")
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

st.sidebar.header("🔍 Filtros")

with engine.connect() as connection:
    query_years = text("""
        SELECT DISTINCT pnm.ANIO_REGISTRO as año
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO IS NOT NULL
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
        AND p.TIPO_PERSONA = 'Estudiante'
        AND pnm.ANIO_REGISTRO BETWEEN 2016 AND 2025
        ORDER BY año DESC
    """)
    result_years = connection.execute(query_years)
    available_years = [str(row[0]) for row in result_years.fetchall()]

    if not available_years:
        st.error("❌ No se encontraron datos de Formación Sábados para estudiantes")
        st.stop()

    selected_year = st.sidebar.selectbox('📅 Año', available_years, index=0)

st.sidebar.divider()
st.sidebar.header("📈 Estadísticas Generales")

with engine.connect() as connection:
    query_total = text("""
        SELECT COUNT(DISTINCT p.ID) as total 
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
        AND p.TIPO_PERSONA = 'Estudiante'
    """)
    total_estudiantes = connection.execute(query_total, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{total_estudiantes:,}")
    
    query_sexo = text("""
        SELECT 
            p.SEXO,
            COUNT(DISTINCT p.ID) as cantidad
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
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

try:
    with engine.connect() as connection:
        # DIAGNÓSTICO - Usando subquery para evitar ONLY_FULL_GROUP_BY
        with st.expander("🔍 Diagnóstico de Datos"):
            st.subheader("Grados disponibles en la base de datos (Formación Sábados)")
            
            query_grados_disponibles = text("""
                SELECT 
                    GRADO,
                    registros_nivel_mcer,
                    estudiantes_unicos
                FROM (
                    SELECT 
                        CASE 
                            WHEN n.GRADO IS NULL OR n.GRADO = '' OR n.GRADO = 'SIN INFORMACION' THEN 'SIN INFORMACION'
                            ELSE n.GRADO
                        END as GRADO,
                        COUNT(DISTINCT pnm.ID) as registros_nivel_mcer,
                        COUNT(DISTINCT p.ID) as estudiantes_unicos
                    FROM Persona_Nivel_MCER pnm
                    INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
                    LEFT JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
                    WHERE pnm.ANIO_REGISTRO = :año
                    AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
                    AND p.TIPO_PERSONA = 'Estudiante'
                    GROUP BY 
                        CASE 
                            WHEN n.GRADO IS NULL OR n.GRADO = '' OR n.GRADO = 'SIN INFORMACION' THEN 'SIN INFORMACION'
                            ELSE n.GRADO
                        END
                ) AS grados_agrupados
                ORDER BY 
                    CASE WHEN GRADO = 'SIN INFORMACION' THEN 1 ELSE 0 END,
                    CASE WHEN GRADO REGEXP '^[0-9]+$' THEN CAST(GRADO AS UNSIGNED) ELSE 999 END,
                    GRADO
            """)
            result_grados = connection.execute(query_grados_disponibles, {"año": int(selected_year)})
            df_grados = pd.DataFrame(result_grados.fetchall(), 
                                    columns=["Grado", "Registros Nivel_MCER", "Estudiantes Únicos"])
            st.dataframe(df_grados, use_container_width=True, hide_index=True)
            
            st.info(f"""
            **Interpretación:**
            - **Grado**: El grado escolar del estudiante para el año {selected_year}
            - **Registros Nivel_MCER**: Total de relaciones persona-nivel registradas
            - **Estudiantes Únicos**: Cantidad de estudiantes diferentes en ese grado
            
            ℹ️ Un estudiante puede aparecer en múltiples años con diferentes grados a medida que avanza en su educación.
            """)
        
        # CONSULTA PRINCIPAL - Usando subquery para evitar ONLY_FULL_GROUP_BY
        query = text("""
            SELECT 
                GRADO,
                SEXO,
                cantidad
            FROM (
                SELECT 
                    CASE 
                        WHEN n.GRADO IS NULL OR n.GRADO = '' OR n.GRADO = 'SIN INFORMACION' THEN 'SIN INFORMACION'
                        ELSE n.GRADO
                    END as GRADO,
                    p.SEXO,
                    COUNT(DISTINCT pnm.ID) as cantidad
                FROM Persona_Nivel_MCER pnm
                INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
                LEFT JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
                WHERE pnm.ANIO_REGISTRO = :año
                AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion sabados%'
                AND p.TIPO_PERSONA = 'Estudiante'
                AND p.SEXO IS NOT NULL
                AND p.SEXO != ''
                AND p.SEXO != 'SIN INFORMACION'
                GROUP BY 
                    CASE 
                        WHEN n.GRADO IS NULL OR n.GRADO = '' OR n.GRADO = 'SIN INFORMACION' THEN 'SIN INFORMACION'
                        ELSE n.GRADO
                    END,
                    p.SEXO
            ) AS datos_base
            ORDER BY 
                CASE WHEN GRADO = 'SIN INFORMACION' THEN 1 ELSE 0 END,
                CASE WHEN GRADO REGEXP '^[0-9]+$' THEN CAST(GRADO AS UNSIGNED) ELSE 999 END,
                GRADO, 
                SEXO
        """)
        
        result = connection.execute(query, {"año": int(selected_year)})
        df = pd.DataFrame(result.fetchall(), columns=["GRADO", "SEXO", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos para el año {selected_year}")
            st.stop()

        # Mostrar datos crudos para verificación
        with st.expander("📊 Datos crudos de la consulta"):
            st.write("**Vista previa de los datos:**")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.write(f"**Total de registros:** {len(df)}")
            st.write(f"**Grados únicos encontrados:** {sorted(df['GRADO'].unique())}")
            st.write(f"**Sexos únicos:** {sorted(df['SEXO'].unique())}")
            st.write(f"**Total de inscripciones:** {df['cantidad'].sum()}")

        # Procesamiento de datos
        df['SEXO_NORMALIZADO'] = df['SEXO'].str.upper().str.strip()
        
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
        df_agrupado = df.groupby(['GRADO', 'SEXO_CATEGORIA'])['cantidad'].sum().reset_index()
        
        # Ordenar grados numéricamente
        def ordenar_grado(grado):
            if grado == 'SIN INFORMACION':
                return (1, 0, '')
            elif str(grado).isdigit():
                return (0, int(grado), grado)
            else:
                return (2, 0, grado)
        
        grados_unicos = sorted(df_agrupado['GRADO'].unique(), key=ordenar_grado)
        
        masculino_por_grado = []
        femenino_por_grado = []
        otro_por_grado = []
        
        for grado in grados_unicos:
            masc = df_agrupado[(df_agrupado['GRADO'] == grado) & (df_agrupado['SEXO_CATEGORIA'] == 'Masculino')]
            masculino_por_grado.append(masc['cantidad'].sum() if not masc.empty else 0)
            
            fem = df_agrupado[(df_agrupado['GRADO'] == grado) & (df_agrupado['SEXO_CATEGORIA'] == 'Femenino')]
            femenino_por_grado.append(fem['cantidad'].sum() if not fem.empty else 0)
            
            otro = df_agrupado[(df_agrupado['GRADO'] == grado) & (df_agrupado['SEXO_CATEGORIA'] == 'Otro')]
            otro_por_grado.append(otro['cantidad'].sum() if not otro.empty else 0)
        
        total_por_grado = [m + f + o for m, f, o in zip(masculino_por_grado, femenino_por_grado, otro_por_grado)]
        
        st.sidebar.header(f"📊 Por Grado - {selected_year}")
        st.sidebar.write(f"**Total de grados:** {len(grados_unicos)}")
        st.sidebar.write(f"**Grados:** {', '.join(map(str, grados_unicos))}")

        # GRÁFICO PRINCIPAL
        st.header(f"📊 Distribución por Sexo y Grado - Formación Sábados - Año {selected_year}")
        
        st.info(f"""
        📌 **Nota importante**: Este gráfico muestra las **inscripciones/registros** de estudiantes por grado para el año {selected_year}.
        Un mismo estudiante puede aparecer en diferentes años con diferentes grados a medida que avanza en su educación.
        """)
        
        # Ajustar altura según cantidad de grados
        altura_grafico = max(10, len(grados_unicos) * 0.8)
        fig, ax = plt.subplots(figsize=(16, altura_grafico))
        y_pos = np.arange(len(grados_unicos))
        
        bars_masc = ax.barh(y_pos, masculino_por_grado, height=0.7,
                           label='Masculino', color='#3498db', 
                           edgecolor='black', linewidth=1.2)
        
        bars_fem = ax.barh(y_pos, femenino_por_grado, height=0.7,
                          left=masculino_por_grado,
                          label='Femenino', color='#e74c3c',
                          edgecolor='black', linewidth=1.2)
        
        # Agregar valores en las barras
        for i, (masc, fem, total) in enumerate(zip(masculino_por_grado, femenino_por_grado, total_por_grado)):
            if masc > 0:
                ax.text(masc / 2, i, f'{int(masc)}',
                       ha='center', va='center',
                       color='white', fontsize=9, fontweight='bold')
            if fem > 0:
                ax.text(masc + fem / 2, i, f'{int(fem)}',
                       ha='center', va='center',
                       color='white', fontsize=9, fontweight='bold')
            if total > 0:
                ax.text(masc + fem, i, f'  {int(total)}',
                       ha='left', va='center',
                       color='black', fontsize=9, fontweight='bold')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(grados_unicos, fontsize=10)
        ax.set_xlabel('Cantidad de Registros', fontsize=13, fontweight='bold')
        ax.set_ylabel('Grado', fontsize=13, fontweight='bold')
        ax.set_title(f'Distribución de Estudiantes por Sexo y Grado - Formación Sábados\nAño {selected_year}',
                    fontsize=16, fontweight='bold', pad=20)
        
        max_val = max(total_por_grado) if total_por_grado else 1
        ax.set_xlim(0, max_val * 1.15)
        
        ax.legend(loc='upper right', fontsize=12, framealpha=0.9)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig)

        # Tabla resumen
        st.header("📋 Tabla Resumen por Grado")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Datos por Grado")
            tabla_data = []
            total_general = 0
            total_masc = 0
            total_fem = 0
            
            for i, grado in enumerate(grados_unicos):
                masc = masculino_por_grado[i]
                fem = femenino_por_grado[i]
                total = total_por_grado[i]
                total_general += total
                total_masc += masc
                total_fem += fem
                porcentaje = (total / sum(total_por_grado) * 100) if sum(total_por_grado) > 0 else 0
                
                tabla_data.append({
                    'Grado': grado,
                    'Masculino': int(masc),
                    'Femenino': int(fem),
                    'Total': int(total),
                    'Porcentaje': f"{porcentaje:.1f}%"
                })
            
            tabla_data.append({
                'Grado': 'TOTAL',
                'Masculino': int(total_masc),
                'Femenino': int(total_fem),
                'Total': int(total_general),
                'Porcentaje': '100.0%'
            })
            
            df_tabla = pd.DataFrame(tabla_data)
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 Distribución por Sexo")
            
            st.metric("Total Masculino", f"{int(total_masc):,}", 
                     f"{(total_masc/total_general*100):.1f}%")
            st.metric("Total Femenino", f"{int(total_fem):,}", 
                     f"{(total_fem/total_general*100):.1f}%")
            
            fig_pie, ax_pie = plt.subplots(figsize=(7, 7))
            ax_pie.pie([total_masc, total_fem],
                      labels=['Masculino', 'Femenino'],
                      autopct='%1.1f%%',
                      colors=['#3498db', '#e74c3c'],
                      startangle=90,
                      textprops={'fontsize': 12, 'fontweight': 'bold'})
            ax_pie.set_title('Distribución por Sexo', fontsize=14, fontweight='bold', pad=20)
            st.pyplot(fig_pie)

        # Gráfico vertical
        st.header("📊 Vista Alternativa - Barras Verticales")
        
        fig_stack, ax_stack = plt.subplots(figsize=(max(14, len(grados_unicos) * 1.2), 8))
        
        x_pos = np.arange(len(grados_unicos))
        width = 0.6
        
        bars1 = ax_stack.bar(x_pos, masculino_por_grado, width, 
                            label='Masculino', color='#3498db',
                            edgecolor='black', linewidth=1.2)
        
        bars2 = ax_stack.bar(x_pos, femenino_por_grado, width, 
                            bottom=masculino_por_grado,
                            label='Femenino', color='#e74c3c',
                            edgecolor='black', linewidth=1.2)
        
        for i, total in enumerate(total_por_grado):
            ax_stack.text(i, total, f'{int(total)}',
                         ha='center', va='bottom',
                         fontsize=11, fontweight='bold', color='#2c3e50')
        
        ax_stack.set_xlabel('Grado', fontsize=13, fontweight='bold')
        ax_stack.set_ylabel('Cantidad de Registros', fontsize=13, fontweight='bold')
        ax_stack.set_title(f'Distribución por Grado (Apilado Vertical) - Formación Sábados - Año {selected_year}',
                          fontsize=16, fontweight='bold', pad=20)
        ax_stack.set_xticks(x_pos)
        ax_stack.set_xticklabels(grados_unicos, rotation=45, ha='right', fontsize=10)
        ax_stack.legend(loc='upper right', fontsize=12)
        ax_stack.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig_stack)

        with st.expander("🔍 Ver datos agrupados completos"):
            st.dataframe(df_agrupado.sort_values(['GRADO', 'SEXO_CATEGORIA']), use_container_width=True, hide_index=True)
        
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Información del reporte:**
        - **Curso**: Formación Sábados
        - **Tipo de población**: Estudiante
        - **Año**: {selected_year}
        - **Total registros**: {int(total_general):,}
        - **Total grados distintos**: {len(grados_unicos)}
        - **Grados encontrados**: {', '.join(map(str, grados_unicos))}
        - **Masculino**: {int(total_masc):,} ({(total_masc/total_general*100):.1f}%)
        - **Femenino**: {int(total_fem):,} ({(total_fem/total_general*100):.1f}%)
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())
