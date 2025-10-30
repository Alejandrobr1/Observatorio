import sys
import os
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime


# Configurar streamlit primero
st.set_page_config(layout="wide")
st.title("Estudiantes por Nivel MCER y Sexo")


# Configuración de la conexión a la base de datos
@st.cache_resource
def get_database_connection():
    """Crear y cachear la conexión a la base de datos"""
    try:
        engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"Error al conectar a la base de datos: {str(e)}")
        st.error("""
        Verifica que:
        1. El servidor MySQL esté corriendo en el puerto 3308
        2. Las credenciales sean correctas (usuario: root, contraseña: 123456)
        3. La base de datos 'observatorio_bilinguismo' exista
        """)
        raise e


# Inicializar la conexión
try:
    engine = get_database_connection()
    st.sidebar.success("✅ Conexión a la base de datos establecida")
except Exception as e:
    st.error("No se pudo establecer la conexión a la base de datos")
    st.exception(e)
    st.stop()


# --- Diagnóstico en Sidebar ---
st.sidebar.header("📊 Diagnóstico General")


with engine.connect() as connection:
    # Verificar total de personas
    query_total = text("SELECT COUNT(*) as total FROM Personas WHERE TIPO_PERSONA = 'Estudiante'")
    total_personas = connection.execute(query_total).fetchone()[0]
    st.sidebar.metric("Total estudiantes en BD", f"{total_personas:,}")
    
    # Verificar personas con nivel MCER
    query_nivel = text("""
        SELECT COUNT(DISTINCT p.NUMERO_DOCUMENTO) as total 
        FROM Personas p
        INNER JOIN Nivel_MCER n ON p.NIVEL_MCER_ID = n.ID
        WHERE p.TIPO_PERSONA = 'Estudiante' 
        AND n.NIVEL_MCER IS NOT NULL
    """)
    personas_con_nivel = connection.execute(query_nivel).fetchone()[0]
    st.sidebar.metric("Estudiantes con nivel MCER", f"{personas_con_nivel:,}")


st.sidebar.divider()


# --- Distribución por Nivel MCER y Año ---
st.header("Distribución por Nivel MCER, Sexo y Año")


try:
    with engine.connect() as connection:
        # Filtro solo con 2025 y 2023
        available_years = ['2025', '2023']
        selected_year = st.selectbox(
            'Seleccionar año',
            available_years,
            index=0,  # Por defecto muestra 2025
            help="Selecciona un año para ver la distribución de estudiantes por nivel MCER y sexo"
        )


        # Consulta para obtener estudiantes por nivel MCER y SEXO del año seleccionado
        query = text(f"""
            WITH RankedRecords AS (
                SELECT 
                    p.NUMERO_DOCUMENTO,
                    p.SEXO,
                    n.NIVEL_MCER,
                    YEAR(n.FECHA_ACTUAL) AS AÑO,
                    ROW_NUMBER() OVER(
                        PARTITION BY p.NUMERO_DOCUMENTO, YEAR(n.FECHA_ACTUAL) 
                        ORDER BY n.FECHA_ACTUAL DESC
                    ) as rn
                FROM Personas p
                INNER JOIN Nivel_MCER n ON p.NIVEL_MCER_ID = n.ID
                WHERE p.TIPO_PERSONA = 'Estudiante'
                    AND n.NIVEL_MCER IS NOT NULL
                    AND p.SEXO IS NOT NULL
                    AND p.SEXO != ''
                    AND n.FECHA_ACTUAL IS NOT NULL
                    AND YEAR(n.FECHA_ACTUAL) = {selected_year}
            )
            SELECT 
                NIVEL_MCER,
                SEXO,
                COUNT(DISTINCT NUMERO_DOCUMENTO) as cantidad
            FROM RankedRecords 
            WHERE rn = 1
            GROUP BY NIVEL_MCER, SEXO
            ORDER BY NIVEL_MCER, SEXO
        """)
        
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["NIVEL_MCER", "SEXO", "cantidad"])


        # Verificar si hay datos
        if df.empty:
            st.warning(f"⚠️ No hay datos disponibles para el año {selected_year}")
            st.info("Por favor, selecciona otro año o verifica que existan registros en la base de datos.")
        else:
            # Filtrar solo A1, A2 y SIN DIAGNOSTICO
            df_filtrado = df[df['NIVEL_MCER'].isin(['A1', 'A2', 'SIN DIAGNOSTICO'])]
            
            if df_filtrado.empty:
                st.warning(f"⚠️ No hay estudiantes clasificados como A1, A2 o SIN DIAGNOSTICO en el año {selected_year}")
            else:
                # Calcular totales
                total_estudiantes = df_filtrado['cantidad'].sum()
                
                # --- ESTADÍSTICAS EN EL SIDEBAR ---
                st.sidebar.header(f"📈 Estadísticas - {selected_year}")
                st.sidebar.metric(
                    f"Total estudiantes {selected_year}", 
                    f"{int(total_estudiantes):,}",
                    help=f"Estudiantes A1, A2 y Sin Diagnóstico en {selected_year}"
                )
                
                # Mostrar desglose por nivel y sexo
                st.sidebar.write("**Desglose por nivel y sexo:**")
                for nivel in ['A1', 'A2', 'SIN DIAGNOSTICO']:
                    nivel_data = df_filtrado[df_filtrado['NIVEL_MCER'] == nivel]
                    if not nivel_data.empty:
                        total_nivel = nivel_data['cantidad'].sum()
                        st.sidebar.write(f"**{nivel}:** {int(total_nivel):,}")
                        
                        for _, row in nivel_data.iterrows():
                            sexo = row['SEXO']
                            cantidad = int(row['cantidad'])
                            st.sidebar.write(f"  • {sexo}: {cantidad:,}")
                
                
                st.success(f"✅ Se encontraron datos de estudiantes para el año {selected_year}")


                # Preparar datos para el gráfico de barras apiladas
                niveles_orden = ['A1', 'A2', 'SIN DIAGNOSTICO']
                niveles_disponibles = [n for n in niveles_orden if n in df_filtrado['NIVEL_MCER'].values]
                
                # Crear diccionarios para masculino y femenino por nivel
                masculino_por_nivel = {}
                femenino_por_nivel = {}
                
                for nivel in niveles_disponibles:
                    nivel_data = df_filtrado[df_filtrado['NIVEL_MCER'] == nivel]
                    
                    # Buscar masculino
                    masc_data = nivel_data[
                        nivel_data['SEXO'].str.contains('Masculino|^M$', case=False, na=False, regex=True)
                    ]
                    masculino_por_nivel[nivel] = masc_data['cantidad'].sum() if not masc_data.empty else 0
                    
                    # Buscar femenino
                    fem_data = nivel_data[
                        nivel_data['SEXO'].str.contains('Femenino|^F$', case=False, na=False, regex=True)
                    ]
                    femenino_por_nivel[nivel] = fem_data['cantidad'].sum() if not fem_data.empty else 0


                # Crear gráfico de barras apiladas
                fig, ax = plt.subplots(figsize=(12, 7))
                
                x = np.arange(len(niveles_disponibles))
                width = 0.6
                
                # Obtener valores para masculino y femenino
                masculino_vals = [masculino_por_nivel[n] for n in niveles_disponibles]
                femenino_vals = [femenino_por_nivel[n] for n in niveles_disponibles]
                
                # Crear barras apiladas
                bars1 = ax.bar(x, masculino_vals, width, label='Masculino', 
                             color='#3498db', edgecolor='black', linewidth=1.5)
                bars2 = ax.bar(x, femenino_vals, width, bottom=masculino_vals, 
                             label='Femenino', color='#e74c3c', edgecolor='black', linewidth=1.5)
                
                # Añadir etiquetas en las barras
                for i, nivel in enumerate(niveles_disponibles):
                    masc_val = masculino_vals[i]
                    fem_val = femenino_vals[i]
                    total_val = masc_val + fem_val
                    
                    # Etiqueta para masculino (parte inferior)
                    if masc_val > 0:
                        ax.text(i, masc_val/2, f'{int(masc_val)}',
                               ha='center', va='center',
                               color='white', fontsize=12, fontweight='bold')
                    
                    # Etiqueta para femenino (parte superior)
                    if fem_val > 0:
                        ax.text(i, masc_val + fem_val/2, f'{int(fem_val)}',
                               ha='center', va='center',
                               color='white', fontsize=12, fontweight='bold')
                    
                    # Total encima de la barra
                    ax.text(i, total_val, f'Total: {int(total_val)}',
                           ha='center', va='bottom',
                           fontsize=11, fontweight='bold')
                
                # Configurar ejes y título
                ax.set_xlabel('Nivel MCER', fontsize=13, fontweight='bold')
                ax.set_ylabel('Cantidad de Estudiantes', fontsize=13, fontweight='bold')
                ax.set_title(f'Distribución por Nivel MCER y Sexo - Año {selected_year}', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xticks(x)
                ax.set_xticklabels(niveles_disponibles)
                ax.legend(loc='upper right', fontsize=11)
                ax.grid(axis='y', alpha=0.3, linestyle='--')
                
                # Ajustar límite del eje Y
                max_val = max([masculino_vals[i] + femenino_vals[i] for i in range(len(niveles_disponibles))])
                ax.set_ylim(0, max_val * 1.15)
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Tabla de datos detallados
                st.subheader(f"Datos detallados - Año {selected_year}")
                
                # Crear tabla resumen con columnas para cada sexo
                tabla_data = []
                for nivel in niveles_disponibles:
                    masc = masculino_por_nivel[nivel]
                    fem = femenino_por_nivel[nivel]
                    total = masc + fem
                    
                    tabla_data.append({
                        'Nivel MCER': nivel,
                        'Masculino': int(masc),
                        'Femenino': int(fem),
                        'Total': int(total),
                        'Porcentaje': f"{(total/total_estudiantes*100):.1f}%"
                    })
                
                df_resumen = pd.DataFrame(tabla_data)
                
                # Añadir fila de totales
                total_masc = sum(masculino_vals)
                total_fem = sum(femenino_vals)
                df_resumen.loc[len(df_resumen)] = ['TOTAL', int(total_masc), int(total_fem), 
                                                    int(total_estudiantes), '100.0%']
                
                st.dataframe(df_resumen, use_container_width=True, hide_index=True)
                
                # Mostrar todos los datos originales (información adicional)
                with st.expander("Ver datos completos por nivel y sexo"):
                    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)


except Exception as e:
    st.error("Error al cargar los datos")
    st.exception(e)
    
    # Mostrar más detalles del error
    import traceback
    st.code(traceback.format_exc())
