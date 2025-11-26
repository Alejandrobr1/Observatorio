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
st.set_page_config(layout="wide", page_title="Dashboard Participación Comfenalco por Sede Nodal")
st.title("📊 Participación de Estudiantes por Sede Nodal (Comfenalco)")
 
# --- State and Navigation ---
if 'population_filter' not in st.session_state:
    st.session_state.population_filter = "Estudiantes Comfenalco"

def create_nav_buttons(selected_pop):
    nav_cols = st.columns(8)
    with nav_cols[0]:
        st.page_link("app.py", label="Inicio", icon="🏠")

    if selected_pop == "Estudiantes Comfenalco":
        links = {
            "Sede Nodal": "pages/1p-estudiantes_matriculados_por_sede_nodal.py",
            "Jornada/Día": "pages/2p-estudiantes_por_jornada_dia.py",
            "Población": "pages/3p-estudiantes_por_poblacion.py",
            "Participación %": "pages/4p-estudiantes_matriculados_sede_porcentaje.py",
            "Etapas (Pastel)": "pages/5p-comparativa_etapas_por_sede.py",
            "Etapas (Barras)": "pages/6p-comparativa_etapas_barras.py",
            "Escuela Nueva (Sede)": "pages/7p-estudiantes_escuela_nueva.py",
            "Escuela Nueva (IE)": "pages/8p-estudiantes_por_institucion.py"
        }
        # Re-ajustar columnas para acomodar todos los botones
        nav_cols = st.columns(len(links) + 1)
        with nav_cols[0]:
            st.page_link("app.py", label="Inicio", icon="🏠")
        for i, (label, page) in enumerate(links.items()):
            with nav_cols[i+1]:
                st.page_link(page, label=label)

    elif selected_pop == "Docentes":
        with nav_cols[1]:
            st.page_link("pages/9p-docentes_por_nivel.py", label="Docentes por Nivel", icon="🎓")
        with nav_cols[2]:
            st.page_link("pages/10p-docentes_por_institucion.py", label="Docentes por Institución", icon="🏫")

    elif selected_pop == "Estudiantes Colombo":
        with nav_cols[1]:
            st.page_link("pages/11p-colombo_por_institucion.py", label="Colombo por Institución", icon="🏫")
        with nav_cols[2]:
            st.page_link("pages/12p-colombo_por_nivel.py", label="Colombo por Nivel", icon="📈")

create_nav_buttons(st.session_state.population_filter)
st.markdown("---")

@st.cache_resource
def get_engine():
    # En producción (Streamlit Cloud), lee desde st.secrets
    db_user = st.secrets["DB_USER"]
    db_pass = st.secrets["DB_PASS"]
    db_host = st.secrets["DB_HOST"]
    db_port = st.secrets["DB_PORT"]
    db_name = st.secrets["DB_NAME"]
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string, pool_pre_ping=True)

# Inicializar conexión
try:
    engine = get_engine()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

# --- Lógica de Estado y Filtros ---

@st.cache_data
def get_available_years(_engine, prefix):
    table_name = "Estudiantes_2016_2019" # Tabla consolidada
    if prefix == "Estudiantes":
        with _engine.connect() as connection:
            if _engine.dialect.has_table(connection, table_name):
                query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} ORDER BY FECHA DESC")
                years = [row[0] for row in connection.execute(query_years).fetchall()]
                if years:
                    return years
                st.warning(f"La tabla '{table_name}' no contiene años en la columna 'FECHA'. Usando año por defecto.")
                return [pd.Timestamp.now().year] # Devuelve el año actual si no hay datos
    else: # Para Docentes
        with _engine.connect() as connection:
            query_tables = text(f"SHOW TABLES LIKE '{prefix}_%'")
            years = [row[0].split('_')[1] for row in connection.execute(query_tables).fetchall() if len(row[0].split('_')) > 1 and row[0].split('_')[1].isdigit()]
            if years:
                return sorted(years, reverse=True)
    return []

st.sidebar.header("Filtros")
selected_population = st.sidebar.selectbox(
    "Filtrar por tipo de población",
    ["Estudiantes Comfenalco", "Estudiantes Colombo", "Docentes"],
    index=["Estudiantes Comfenalco", "Estudiantes Colombo", "Docentes"].index(st.session_state.population_filter),
    key="population_filter",
    help="Selecciona el grupo de datos a visualizar."
)
st.sidebar.divider()

if selected_population != "Estudiantes Comfenalco":
    st.info(f"Este dashboard es para 'Estudiantes Comfenalco'. Por favor, selecciona esa opción en el filtro de población para ver los datos.")
    st.stop()

population_prefix = "Estudiantes"
available_years = get_available_years(engine, population_prefix)

if not available_years:
    st.warning(f"⚠️ No se encontraron datos para '{selected_population}'.")
    st.stop()

# FORZAR REINICIO DEL AÑO: Si el año guardado en la sesión no es válido para
# los datos de ESTA PÁGINA, se reinicia al año más reciente disponible.
if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.info(f"**Población:** {selected_population}")
st.sidebar.info(f"**Año:** {selected_year}")
st.sidebar.divider()

# --- Carga de Datos ---
@st.cache_data
def load_data(_engine, prefix, year):
    # Si son estudiantes, usar la tabla consolidada. Si no, mantener la lógica anterior.
    table_name = "Estudiantes_2016_2019" if prefix == "Estudiantes" else f"{prefix}_{year}"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(columns=["SEDE_NODAL", "cantidad"]), 0, 0
        params = {'year': year}

        query = text(f"""
            SELECT 
                SEDE_NODAL, COALESCE(SUM(MATRICULADOS), 0) as cantidad
            FROM {table_name}
            WHERE SEDE_NODAL IS NOT NULL AND SEDE_NODAL != '' AND SEDE_NODAL != 'SIN INFORMACION'
              AND ETAPA = '1'
              AND FECHA = :year
            GROUP BY SEDE_NODAL
            ORDER BY cantidad DESC
        """)
        result = connection.execute(query, params)
        df = pd.DataFrame(result.fetchall(), columns=["SEDE_NODAL", "cantidad"])
        
        # Métricas
        total_matriculados = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE FECHA = :year AND ETAPA = '1'"), params).scalar() or 0
        total_sedes = connection.execute(text(f"SELECT COUNT(DISTINCT SEDE_NODAL) FROM {table_name} WHERE FECHA = :year AND ETAPA = '1' AND SEDE_NODAL IS NOT NULL AND SEDE_NODAL != ''"), params).scalar() or 0
        
        return df, total_matriculados, total_sedes

try:
    df, total_matriculados, total_sedes = load_data(engine, population_prefix, selected_year)

    # --- Visualización ---
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Matriculados (Etapa 1, {selected_year})", f"{int(total_matriculados):,}")
    st.sidebar.metric(f"Total Sedes Nodales ({selected_year})", f"{total_sedes:,}")
    st.sidebar.divider()

    if df.empty:
        st.warning(f"⚠️ No hay datos de matriculados por sede nodal para el año {selected_year} en la Etapa 1.")
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
                        st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

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

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)
    with st.expander("Ver detalles técnicos del error"):
        st.code(traceback.format_exc())