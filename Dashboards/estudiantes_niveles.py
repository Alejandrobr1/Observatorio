import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# Limpiar cache al inicio
st.cache_data.clear()
st.cache_resource.clear()

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard MCER por Genero")
st.title("📊 Estudiantes por Nivel MCER y Genero")

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

# Sidebar - Diagnóstico y filtros
st.sidebar.header("🔍 Filtros")

with engine.connect() as connection:
    # Obtener tipos de persona disponibles
    query_tipos = text("""
        SELECT DISTINCT p.TIPO_PERSONA
        FROM Personas p
        INNER JOIN Persona_Nivel_MCER pnm ON p.ID = pnm.PERSONA_ID
        WHERE p.TIPO_PERSONA IS NOT NULL
        AND p.TIPO_PERSONA != ''
        AND p.TIPO_PERSONA != 'SIN INFORMACION'
        ORDER BY p.TIPO_PERSONA
    """)
    result_tipos = connection.execute(query_tipos)
    available_tipos = ['TODOS'] + [row[0] for row in result_tipos.fetchall()]
    
    # Filtro de tipo de persona
    selected_tipo = st.sidebar.selectbox(
        '👥 Tipo de Población',
        available_tipos,
        index=0
    )
    
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
    
    # NUEVO: Obtener instituciones disponibles
    query_instituciones = text("""
        SELECT DISTINCT i.NOMBRE_INSTITUCION
        FROM Instituciones i
        INNER JOIN Personas p ON p.INSTITUCION_ID = i.ID
        INNER JOIN Persona_Nivel_MCER pnm ON pnm.PERSONA_ID = p.ID
        WHERE i.NOMBRE_INSTITUCION IS NOT NULL
        AND i.NOMBRE_INSTITUCION != ''
        ORDER BY i.NOMBRE_INSTITUCION
    """)
    result_instituciones = connection.execute(query_instituciones)
    available_instituciones = ['TODAS'] + [row[0] for row in result_instituciones.fetchall()]
    
    # NUEVO: Filtro de institución
    selected_institucion = st.sidebar.selectbox(
        '🏫 Institución Educativa',
        available_instituciones,
        index=0
    )

st.sidebar.divider()

# Información general
st.sidebar.header("📈 Estadísticas Generales")

with engine.connect() as connection:
    # Total personas en BD
    query_total = text("SELECT COUNT(*) as total FROM Personas")
    total_personas = connection.execute(query_total).fetchone()[0]
    st.sidebar.metric("Total Personas", f"{total_personas:,}")

    # Personas con nivel MCER
    query_con_nivel = text("""
        SELECT COUNT(DISTINCT pnm.PERSONA_ID) as total 
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
        WHERE n.NIVEL_MCER IS NOT NULL
        AND n.NIVEL_MCER != 'SIN INFORMACION'
    """)
    total_con_nivel = connection.execute(query_con_nivel).fetchone()[0]
    st.sidebar.metric("Con Nivel MCER", f"{total_con_nivel:,}")

st.sidebar.divider()

# Consulta principal CON filtros de TIPO_PERSONA e INSTITUCION
try:
    with engine.connect() as connection:
        # Construir filtros dinámicos
        filtros = []
        query_params = {"año": int(selected_year)}
        
        if selected_tipo != 'TODOS':
            filtros.append("AND p.TIPO_PERSONA = :tipo")
            query_params["tipo"] = selected_tipo
        
        if selected_institucion != 'TODAS':
            filtros.append("AND i.NOMBRE_INSTITUCION = :institucion")
            query_params["institucion"] = selected_institucion
        
        filtros_sql = " ".join(filtros)
        
        # Consulta principal
        query = text(f"""
            SELECT 
                n.NIVEL_MCER,
                p.GENERO,
                COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
            LEFT JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
            WHERE pnm.ANIO_REGISTRO = :año
            AND n.NIVEL_MCER IS NOT NULL
            AND n.NIVEL_MCER != 'SIN INFORMACION'
            AND p.GENERO IS NOT NULL
            AND p.GENERO != ''
            AND p.GENERO != 'SIN INFORMACION'
            {filtros_sql}
            GROUP BY n.NIVEL_MCER, p.GENERO
            ORDER BY n.NIVEL_MCER, p.GENERO
        """)
        
        result = connection.execute(query, query_params)
        df = pd.DataFrame(result.fetchall(), columns=["NIVEL_MCER", "GENERO", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos disponibles con los filtros seleccionados")
            st.info(f"""
            **Filtros aplicados:**
            - Tipo de población: {selected_tipo}
            - Año: {selected_year}
            - Institución: {selected_institucion}
            """)
            st.stop()

        # Obtener niveles únicos
        niveles_disponibles = sorted(df['NIVEL_MCER'].unique())
        total_estudiantes = df['cantidad'].sum()

        # Mostrar estadísticas del filtro actual
        titulo_filtros = f"{selected_tipo} - {selected_year}"
        if selected_institucion != 'TODAS':
            titulo_filtros += f" - {selected_institucion}"
            
        st.sidebar.header(f"📊 Filtros Activos")
        st.sidebar.metric("Total con Nivel MCER", f"{int(total_estudiantes):,}")
        
        # Desglose por nivel
        st.sidebar.write("**Por Nivel MCER:**")
        for nivel in niveles_disponibles:
            nivel_data = df[df['NIVEL_MCER'] == nivel]
            total_nivel = nivel_data['cantidad'].sum()
            st.sidebar.write(f"• **{nivel}**: {int(total_nivel):,}")

        # Preparar datos para el gráfico
        masculino_por_nivel = {}
        femenino_por_nivel = {}

        for nivel in niveles_disponibles:
            nivel_data = df[df['NIVEL_MCER'] == nivel]
            
            # Filtrar masculinos
            masc_data = nivel_data[
                nivel_data['GENERO'].str.upper().str.contains('M|MASCULINO|HOMBRE', na=False, regex=True)
            ]
            masculino_por_nivel[nivel] = masc_data['cantidad'].sum() if not masc_data.empty else 0
            
            # Filtrar femeninos
            fem_data = nivel_data[
                nivel_data['GENERO'].str.upper().str.contains('F|FEMENINO|MUJER', na=False, regex=True)
            ]
            femenino_por_nivel[nivel] = fem_data['cantidad'].sum() if not fem_data.empty else 0

        # Crear el gráfico de barras apiladas
        st.header(f"📊 Distribución por Nivel MCER")
        st.subheader(titulo_filtros)
        
        fig, ax = plt.subplots(figsize=(14, 8))

        x = np.arange(len(niveles_disponibles))
        width = 0.65

        masculino_vals = [masculino_por_nivel[n] for n in niveles_disponibles]
        femenino_vals = [femenino_por_nivel[n] for n in niveles_disponibles]

        # Barras apiladas
        bars_masc = ax.bar(x, masculino_vals, width, label='Masculino',
                          color='#3498db', edgecolor='black', linewidth=1.5)
        bars_fem = ax.bar(x, femenino_vals, width, bottom=masculino_vals,
                         label='Femenino', color='#e74c3c', edgecolor='black', linewidth=1.5)

        # Añadir valores en las barras
        for i, nivel in enumerate(niveles_disponibles):
            masc_val = masculino_vals[i]
            fem_val = femenino_vals[i]
            total_val = masc_val + fem_val

            if masc_val > 0:
                ax.text(i, masc_val / 2, f'{int(masc_val)}',
                       ha='center', va='center',
                       color='white', fontsize=11, fontweight='bold')

            if fem_val > 0:
                ax.text(i, masc_val + fem_val / 2, f'{int(fem_val)}',
                       ha='center', va='center',
                       color='white', fontsize=11, fontweight='bold')

            if total_val > 0:
                ax.text(i, total_val, f'Total: {int(total_val)}',
                       ha='center', va='bottom',
                       fontsize=10, fontweight='bold', color='#2c3e50')

        # Configuración del gráfico
        ax.set_xlabel('Nivel MCER', fontsize=14, fontweight='bold')
        ax.set_ylabel('Cantidad de Personas', fontsize=14, fontweight='bold')
        
        titulo_grafico = f'Distribución por Nivel MCER y Genero'
        if selected_institucion != 'TODAS':
            # Acortar nombre si es muy largo
            nombre_corto = selected_institucion[:40] + '...' if len(selected_institucion) > 40 else selected_institucion
            titulo_grafico += f'\n{nombre_corto}'
        
        ax.set_title(titulo_grafico, fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(niveles_disponibles, fontsize=12)
        ax.legend(loc='upper right', fontsize=12, framealpha=0.9)
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.7)

        max_val = max([masculino_vals[i] + femenino_vals[i] for i in range(len(niveles_disponibles))]) if niveles_disponibles else 1
        ax.set_ylim(0, max_val * 1.2)

        plt.tight_layout()
        st.pyplot(fig)

        # Tabla resumen
        st.header("📋 Tabla Resumen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Datos por Nivel")
            tabla_data = []
            for nivel in niveles_disponibles:
                masc = masculino_por_nivel[nivel]
                fem = femenino_por_nivel[nivel]
                total = masc + fem
                porcentaje = (total / total_estudiantes * 100) if total_estudiantes > 0 else 0

                tabla_data.append({
                    'Nivel MCER': nivel,
                    'Masculino': int(masc),
                    'Femenino': int(fem),
                    'Total': int(total),
                    'Porcentaje': f"{porcentaje:.1f}%"
                })

            df_resumen = pd.DataFrame(tabla_data)
            
            total_masc = sum(masculino_vals)
            total_fem = sum(femenino_vals)
            df_resumen.loc[len(df_resumen)] = ['TOTAL', int(total_masc), int(total_fem),
                                               int(total_estudiantes), '100.0%']
            
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)

        with col2:
            st.subheader("Distribución por Genero")
            
            total_masc = sum(masculino_vals)
            total_fem = sum(femenino_vals)
            
            if total_estudiantes > 0:
                porc_masc = (total_masc / total_estudiantes * 100)
                porc_fem = (total_fem / total_estudiantes * 100)
                
                st.metric("Total Masculino", f"{int(total_masc):,}", 
                         f"{porc_masc:.1f}%")
                st.metric("Total Femenino", f"{int(total_fem):,}", 
                         f"{porc_fem:.1f}%")
                
                fig_pie, ax_pie = plt.subplots(figsize=(6, 6))
                ax_pie.pie([total_masc, total_fem], 
                          labels=['Masculino', 'Femenino'],
                          autopct='%1.1f%%',
                          colors=['#3498db', '#e74c3c'],
                          startangle=90,
                          textprops={'fontsize': 12, 'fontweight': 'bold'})
                ax_pie.set_title('Distribución por Genero', fontsize=14, fontweight='bold', pad=20)
                st.pyplot(fig_pie)

        with st.expander("🔍 Ver datos detallados"):
            st.dataframe(df.sort_values(['NIVEL_MCER', 'GENERO']), use_container_width=True, hide_index=True)
        
        st.success(f"""
        ✅ **Datos cargados exitosamente**
        
        📌 **Filtros aplicados:**
        - **Tipo de población**: {selected_tipo}
        - **Año**: {selected_year}
        - **Institución**: {selected_institucion}
        - **Total personas**: {int(total_estudiantes):,}
        - **Niveles MCER**: {', '.join(niveles_disponibles)}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        import traceback
        st.code(traceback.format_exc())
