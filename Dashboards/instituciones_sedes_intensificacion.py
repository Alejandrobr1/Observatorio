import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Instituciones y Sedes Nodales - Intensificación")
st.title("🏫 Distribución de Estudiantes por Institución y Sede Nodal - Intensificación")

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
    # Obtener años disponibles FILTRADO POR INTENSIFICACIÓN
    query_years = text("""
        SELECT DISTINCT pnm.ANIO_REGISTRO as año
        FROM Persona_Nivel_MCER pnm
        WHERE pnm.ANIO_REGISTRO IS NOT NULL
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
        ORDER BY año DESC
    """)
    result_years = connection.execute(query_years)
    available_years = [str(row[0]) for row in result_years.fetchall()]

    if not available_years:
        st.error("No se encontraron años en la base de datos con intensificación")
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
    # Total estudiantes FILTRADO POR INTENSIFICACIÓN
    query_total = text("""
        SELECT COUNT(DISTINCT p.ID) as total 
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        INNER JOIN Sedes s ON s.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND p.TIPO_PERSONA = 'Estudiante'
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
    """)
    total_estudiantes = connection.execute(query_total, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Estudiantes ({selected_year})", f"{total_estudiantes:,}")
    
    # Total instituciones FILTRADO POR INTENSIFICACIÓN
    query_inst = text("""
        SELECT COUNT(DISTINCT i.ID) as total
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        INNER JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
        INNER JOIN Sedes s ON s.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND i.NOMBRE_INSTITUCION IS NOT NULL
        AND i.NOMBRE_INSTITUCION != ''
        AND i.NOMBRE_INSTITUCION != 'SIN INFORMACION'
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
    """)
    total_inst = connection.execute(query_inst, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Instituciones ({selected_year})", f"{total_inst:,}")
    
    # Total sedes nodales FILTRADO POR INTENSIFICACIÓN
    query_sedes = text("""
        SELECT COUNT(DISTINCT s.SEDE_NODAL) as total
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        INNER JOIN Sedes s ON s.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO = :año
        AND s.SEDE_NODAL IS NOT NULL
        AND s.SEDE_NODAL != ''
        AND s.SEDE_NODAL != 'SIN INFORMACION'
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
    """)
    total_sedes = connection.execute(query_sedes, {"año": int(selected_year)}).fetchone()[0]
    st.sidebar.metric(f"Total Sedes Nodales ({selected_year})", f"{total_sedes:,}")

st.sidebar.divider()

# Consulta principal
try:
    with engine.connect() as connection:
        # Consulta para obtener estudiantes por institución y sede nodal FILTRADO POR INTENSIFICACIÓN
        query = text("""
            SELECT 
                i.NOMBRE_INSTITUCION,
                s.SEDE_NODAL,
                COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
            FROM Persona_Nivel_MCER pnm
            INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
            INNER JOIN Instituciones i ON p.INSTITUCION_ID = i.ID
            INNER JOIN Sedes s ON s.PERSONA_ID = p.ID
            WHERE pnm.ANIO_REGISTRO = :año
            AND p.TIPO_PERSONA = 'Estudiante'
            AND i.NOMBRE_INSTITUCION IS NOT NULL
            AND i.NOMBRE_INSTITUCION != ''
            AND i.NOMBRE_INSTITUCION != 'SIN INFORMACION'
            AND s.SEDE_NODAL IS NOT NULL
            AND s.SEDE_NODAL != ''
            AND s.SEDE_NODAL != 'SIN INFORMACION'
            AND LOWER(pnm.NOMBRE_CURSO) LIKE '%intensificacion%'
            GROUP BY i.NOMBRE_INSTITUCION, s.SEDE_NODAL
            ORDER BY i.NOMBRE_INSTITUCION, cantidad DESC
        """)
        
        result = connection.execute(query, {"año": int(selected_year)})
        df = pd.DataFrame(result.fetchall(), columns=["INSTITUCION", "SEDE_NODAL", "cantidad"])

        if df.empty:
            st.warning(f"⚠️ No hay datos de instituciones y sedes para el año {selected_year} - Intensificación")
            st.stop()

        # Obtener lista de instituciones únicas ordenadas por total de estudiantes
        total_por_institucion = df.groupby('INSTITUCION')['cantidad'].sum().sort_values(ascending=True)
        instituciones_ordenadas = total_por_institucion.index.tolist()
        
        # Obtener lista de sedes nodales únicas
        sedes_unicas = sorted(df['SEDE_NODAL'].unique())
        
        # Crear matriz de datos (instituciones x sedes)
        # Cada fila es una institución, cada columna es una sede nodal
        data_matrix = []
        for institucion in instituciones_ordenadas:
            fila = []
            for sede in sedes_unicas:
                valor = df[(df['INSTITUCION'] == institucion) & (df['SEDE_NODAL'] == sede)]['cantidad'].sum()
                fila.append(valor)
            data_matrix.append(fila)
        
        data_matrix = np.array(data_matrix)
        
        # Top instituciones en sidebar
        st.sidebar.header(f"📊 Top 5 Instituciones - {selected_year} - Intensificación")
        top_5 = total_por_institucion.tail(5).sort_values(ascending=False)
        for idx, (inst, total) in enumerate(top_5.items(), 1):
            nombre_corto = inst[:30] + '...' if len(inst) > 30 else inst
            st.sidebar.write(f"**{idx}. {nombre_corto}**")
            st.sidebar.write(f"   {int(total):,} estudiantes")

        # Crear gráfico de barras horizontales apiladas
        st.header(f"📊 Estudiantes por Institución y Sede Nodal - Año {selected_year} - Intensificación")
        
        # Limitar a top 15 instituciones para mejor visualización
        num_instituciones_mostrar = min(15, len(instituciones_ordenadas))
        instituciones_mostrar = instituciones_ordenadas[-num_instituciones_mostrar:]
        data_mostrar = data_matrix[-num_instituciones_mostrar:]
        
        fig, ax = plt.subplots(figsize=(14, max(10, num_instituciones_mostrar * 0.7)))
        
        y_pos = np.arange(len(instituciones_mostrar))
        
        # Colores para cada sede nodal
        colors = plt.cm.Set3(np.linspace(0, 1, len(sedes_unicas)))
        
        # Crear barras apiladas
        left_positions = np.zeros(len(instituciones_mostrar))
        
        for idx_sede, sede in enumerate(sedes_unicas):
            valores_sede = data_mostrar[:, idx_sede]
            
            bars = ax.barh(y_pos, valores_sede, left=left_positions,
                          height=0.7, label=sede, color=colors[idx_sede],
                          edgecolor='black', linewidth=0.5)
            
            # Agregar etiquetas en las barras (solo si el valor es significativo)
            for i, (bar, valor) in enumerate(zip(bars, valores_sede)):
                if valor > 0:
                    # Calcular posición del texto (centro de la barra)
                    x_pos = left_positions[i] + valor / 2
                    # Solo mostrar texto si la barra es lo suficientemente ancha
                    if valor > total_por_institucion[instituciones_mostrar[i]] * 0.05:
                        ax.text(x_pos, i, f'{int(valor)}',
                               ha='center', va='center',
                               color='black', fontsize=8, fontweight='bold')
            
            # Actualizar posiciones para la siguiente sede
            left_positions += valores_sede
        
        # Agregar totales al final de cada barra
        for i, total in enumerate(left_positions):
            if total > 0:
                ax.text(total, i, f'  {int(total):,}',
                       ha='left', va='center',
                       color='black', fontsize=9, fontweight='bold')
        
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
        ax.set_xlabel('Cantidad de Estudiantes', fontsize=13, fontweight='bold')
        ax.set_ylabel('Institución Educativa', fontsize=13, fontweight='bold')
        ax.set_title(f'Distribución de Estudiantes por Institución y Sede Nodal - Intensificación\nAño {selected_year}',
                    fontsize=16, fontweight='bold', pad=20)
        
        # Configurar límite del eje X
        max_val = left_positions.max()
        ax.set_xlim(0, max_val * 1.12)
        
        # Leyenda
        ax.legend(loc='lower right', fontsize=9, ncol=min(3, len(sedes_unicas)),
                 framealpha=0.9, title='Sedes Nodales')
        
        # Grid
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig)

        # Tabla resumen
        st.header("📋 Tabla Detallada por Institución")
        
        # Selector de institución para ver detalle
        institucion_seleccionada = st.selectbox(
            "Selecciona una institución para ver el detalle:",
            instituciones_ordenadas[::-1]  # Invertir para mostrar las más grandes primero
        )
        
        # Filtrar datos de la institución seleccionada
        df_institucion = df[df['INSTITUCION'] == institucion_seleccionada].sort_values('cantidad', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📊 {institucion_seleccionada}")
            
            # Crear tabla
            tabla_data = []
            total_inst = 0
            for idx, row in df_institucion.iterrows():
                sede = row['SEDE_NODAL']
                cantidad = int(row['cantidad'])
                total_inst += cantidad
                
                tabla_data.append({
                    'Sede Nodal': sede,
                    'Estudiantes': f"{cantidad:,}",
                    'Porcentaje': ''  # Calcularemos después
                })
            
            # Calcular porcentajes
            for item in tabla_data:
                cantidad = int(item['Estudiantes'].replace(',', ''))
                porcentaje = (cantidad / total_inst * 100) if total_inst > 0 else 0
                item['Porcentaje'] = f"{porcentaje:.1f}%"
            
            # Agregar fila de total
            tabla_data.append({
                'Sede Nodal': 'TOTAL',
                'Estudiantes': f"{total_inst:,}",
                'Porcentaje': '100.0%'
            })
            
            df_tabla = pd.DataFrame(tabla_data)
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 Distribución")
            
            # Gráfico de pastel para la institución seleccionada
            if not df_institucion.empty:
                fig_pie, ax_pie = plt.subplots(figsize=(7, 7))
                
                explode = tuple([0.02] * len(df_institucion))
                colors_pie = plt.cm.Set3(np.linspace(0, 1, len(df_institucion)))
                
                wedges, texts, autotexts = ax_pie.pie(
                    df_institucion['cantidad'],
                    labels=df_institucion['SEDE_NODAL'],
                    autopct='%1.1f%%',
                    colors=colors_pie,
                    explode=explode,
                    startangle=90,
                    textprops={'fontsize': 9, 'fontweight': 'bold'},
                    shadow=True
                )
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(10)
                
                ax_pie.set_title(f'Distribución por Sede Nodal - Intensificación\n{institucion_seleccionada[:40]}...' 
                               if len(institucion_seleccionada) > 40 else f'Distribución por Sede Nodal - Intensificación\n{institucion_seleccionada}',
                               fontsize=11, fontweight='bold', pad=15)
                
                st.pyplot(fig_pie)

        # Tabla completa de todas las instituciones
        with st.expander("🔍 Ver tabla completa de todas las instituciones"):
            st.write(f"**Total: {len(instituciones_ordenadas)} instituciones**")
            
            # Crear tabla resumen general
            tabla_completa = []
            for institucion in instituciones_ordenadas[::-1]:  # Ordenar de mayor a menor
                df_inst = df[df['INSTITUCION'] == institucion]
                total = df_inst['cantidad'].sum()
                num_sedes = len(df_inst)
                
                tabla_completa.append({
                    'Institución': institucion,
                    'Total Estudiantes': f"{int(total):,}",
                    'Num. Sedes': num_sedes
                })
            
            df_completa = pd.DataFrame(tabla_completa)
            st.dataframe(df_completa, use_container_width=True, hide_index=True)

        # Información adicional
        st.success(f"""
        ✅ **Datos cargados exitosamente - INTENSIFICACIÓN**
        
        📌 **Información del reporte:**
        - **Año**: {selected_year}
        - **Tipo**: Intensificación
        - **Total estudiantes**: {int(total_por_institucion.sum()):,}
        - **Total instituciones**: {len(instituciones_ordenadas)}
        - **Total sedes nodales**: {len(sedes_unicas)}
        - **Sedes nodales**: {', '.join(sedes_unicas)}
        """)

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    
    with st.expander("Ver detalles técnicos del error"):
        import traceback
        st.code(traceback.format_exc())
