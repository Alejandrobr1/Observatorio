import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import create_engine, text
import sys
import os

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Dashboard Participación por Sede Nodal")
st.title("📊 Participación de Estudiantes por Sede Nodal")

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
    st.sidebar.page_link("app.py", label="Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

# --- Lógica de Estado y Filtros ---

@st.cache_data
def get_available_years(_engine, prefix):
    with _engine.connect() as connection:
        query_tables = text(f"SHOW TABLES LIKE '{prefix}_%'")
        result_tables = connection.execute(query_tables)
        return sorted([row[0].split('_')[1] for row in result_tables.fetchall()], reverse=True)

col1, col2 = st.columns([1, 3])
with col1:
    selected_population = st.selectbox(
        "Filtrar por tipo de población",
        ["Estudiantes", "Docentes"],
        key="population_filter",
        help="Selecciona si quieres ver datos de Estudiantes o Docentes."
    )

population_prefix = "Estudiantes" if selected_population == "Estudiantes" else "Docentes"
available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning(f"⚠️ No se encontraron datos para '{selected_population}'.")
    st.stop()

# Inicializar el estado de la sesión para el año si no existe o si cambió la población
if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.header("🔍 Filtros Aplicados")
st.sidebar.info(f"**Población:** {selected_population}")
st.sidebar.info(f"**Año:** {selected_year}")
st.sidebar.divider()

# --- Carga de Datos ---
@st.cache_data
def load_data(_engine, prefix, year):
    table_name = f"{prefix}_{year}"
    with _engine.connect() as connection:
        table_exists_query = text(f"SHOW TABLES LIKE '{table_name}'")
        if connection.execute(table_exists_query).fetchone() is None:
            return pd.DataFrame(columns=["SEDE_NODAL", "cantidad"]), 0, 0
    with _engine.connect() as connection:
        query = text(f"""
            SELECT 
                SEDE_NODAL, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE SEDE_NODAL IS NOT NULL AND SEDE_NODAL != '' AND SEDE_NODAL != 'SIN INFORMACION'
              AND ETAPA = '1'
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=["SEDE_NODAL", "cantidad"])
        
        total_matriculados = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE ETAPA = '1'")).scalar() or 0
        total_sedes = connection.execute(text(f"SELECT COUNT(DISTINCT SEDE_NODAL) FROM {table_name} WHERE ETAPA = '1' AND SEDE_NODAL IS NOT NULL AND SEDE_NODAL != ''")).scalar() or 0
        
        return df, total_matriculados, total_sedes

try:
    df, total_matriculados, total_sedes = load_data(engine, population_prefix, selected_year)

    # --- Visualización ---
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
    st.sidebar.metric(f"Total Sedes Nodales ({selected_year})", f"{total_sedes:,}")
    st.sidebar.divider()

    if df.empty:
        st.warning(f"⚠️ No hay datos de matriculados por sede nodal para el año {selected_year}.")
    else:
        # Convertir cantidad a numérico para evitar errores de tipo
        df['cantidad'] = pd.to_numeric(df['cantidad'])

        st.header(f"📊 Distribución de Matriculados por Sede Nodal - Año {selected_year}")
        
        df_pie = df.copy()
        if len(df_pie) > 10:
            pie_top = df_pie.nlargest(10, 'cantidad')
            otras_sum = df_pie.nsmallest(len(df_pie) - 10, 'cantidad')['cantidad'].sum()
            pie_top.loc[len(pie_top)] = {'SEDE_NODAL': 'Otras Sedes', 'cantidad': otras_sum}
            df_pie = pie_top
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = plt.cm.viridis(np.linspace(0, 1, len(df_pie)))
            explode = [0.05 if i == 0 else 0 for i in range(len(df_pie))]
            wedges, texts, autotexts = ax.pie(
                df_pie['cantidad'], 
                labels=df_pie['SEDE_NODAL'],
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                explode=explode,
                textprops={'fontsize': 10, 'fontweight': 'bold'},
                shadow=True
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
            ax.set_title(f'Participación por Sede Nodal\nAño {selected_year}', 
                        fontsize=18, fontweight='bold', pad=20)
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            # --- Selección de Año con Botones ---
            with st.expander("📅 **Seleccionar Año para Visualizar**", expanded=True):
                st.write("Haz clic en un botón para cambiar el año de los datos mostrados.")
                
                cols_buttons = st.columns(len(available_years))
                
                def set_year(year):
                    st.session_state.selected_year = year

                for i, year in enumerate(available_years):
                    with cols_buttons[i]:
                        button_type = "primary" if year == selected_year else "secondary"
                        st.button(year, key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

            st.divider()

            st.subheader("📋 Resumen")
            df['porcentaje'] = (df['cantidad'] / float(total_matriculados) * 100) if total_matriculados > 0 else 0
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