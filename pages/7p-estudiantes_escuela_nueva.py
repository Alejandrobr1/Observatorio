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
st.set_page_config(layout="wide", page_title="Estudiantes Escuela Nueva")
st.title("📊 Estudiantes por Grupo y Sede de Escuela Nueva")

@st.cache_resource
def get_engine():
    # Lee desde st.secrets
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
    st.sidebar.page_link("app.py", label="Volver al Inicio", icon="🏠")
    st.sidebar.divider()
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

@st.cache_data
def get_available_years(_engine):
    table_name = "Escuela_nueva"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            st.warning(f"La tabla '{table_name}' no existe. No se pueden cargar los años.")
            return []
        query_years = text(f"SELECT DISTINCT FECHA FROM {table_name} ORDER BY FECHA DESC")
        years = [row[0] for row in connection.execute(query_years).fetchall()]
        if years:
            return years
    st.warning(f"No se encontraron años en la tabla '{table_name}'.")
    return []

available_years = get_available_years(engine)

if not available_years:
    st.warning("⚠️ No se encontraron datos para 'Escuela Nueva'.")
    st.stop()

if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
    st.session_state.selected_year = available_years[0]

selected_year = st.session_state.selected_year

st.sidebar.header("🔍 Filtros Aplicados")
st.sidebar.info(f"**Año:** {selected_year}")
st.sidebar.divider()

# --- Función de Visualización ---
def create_bar_chart_and_table(df_data, total_grupo, title):
    st.header(title)
    
    if df_data.empty:
        st.warning("No hay datos para este grupo.")
        return

    df_data['cantidad'] = pd.to_numeric(df_data['cantidad'])
    df_data = df_data[df_data['cantidad'] > 0]

    if df_data.empty:
        st.info("No hay sedes con matriculados para este grupo.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(df_data)))
    bars = ax.bar(df_data['sede'], df_data['cantidad'], color=colors, edgecolor='black', linewidth=1.2)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height):,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Sede', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cantidad de Matriculados', fontsize=12, fontweight='bold')
    ax.set_title('Matriculados por Sede', fontsize=14, fontweight='bold', pad=20)
    plt.xticks(rotation=45, ha="right")
    max_val = df_data['cantidad'].max() if not df_data.empty else 1
    ax.set_ylim(0, float(max_val) * 1.2)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("📋 Resumen")
    df_data['porcentaje'] = (df_data['cantidad'] / float(total_grupo) * 100) if total_grupo > 0 else 0
    df_display = df_data.copy()
    df_display['#'] = range(1, len(df_display) + 1)
    df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
    df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
    df_display = df_display[['#', 'sede', 'cantidad', 'porcentaje']]
    df_display.columns = ['#', 'Sede', 'Matriculados', 'Porcentaje']
    st.dataframe(df_display, use_container_width=True, hide_index=True)

@st.cache_data
def load_escuela_nueva_data(_engine, year):
    table_name = "Escuela_nueva"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 0

        params = {'year': year}
        # Métricas
        total_matriculados = connection.execute(text(f"SELECT SUM(MATRICULADOS) FROM {table_name} WHERE FECHA = :year"), params).scalar() or 0
        total_grupo1 = connection.execute(text(f"SELECT SUM(GRUPO_1) FROM {table_name} WHERE FECHA = :year"), params).scalar() or 0
        total_grupo2 = connection.execute(text(f"SELECT SUM(GRUPO_2) FROM {table_name} WHERE FECHA = :year"), params).scalar() or 0
        total_grupo3 = connection.execute(text(f"SELECT SUM(GRUPO_3) FROM {table_name} WHERE FECHA = :year"), params).scalar() or 0

        # Datos por grupo
        query_g1 = text(f"SELECT SEDE as sede, COALESCE(SUM(GRUPO_1), 0) as cantidad FROM {table_name} WHERE FECHA = :year AND SEDE IS NOT NULL AND SEDE != '' AND SEDE != 'SIN INFORMACION' GROUP BY sede ORDER BY cantidad DESC")
        df_g1 = pd.DataFrame(connection.execute(query_g1, params).fetchall(), columns=["sede", "cantidad"])

        query_g2 = text(f"SELECT SEDE as sede, COALESCE(SUM(GRUPO_2), 0) as cantidad FROM {table_name} WHERE FECHA = :year AND SEDE IS NOT NULL AND SEDE != '' AND SEDE != 'SIN INFORMACION' GROUP BY sede ORDER BY cantidad DESC")
        df_g2 = pd.DataFrame(connection.execute(query_g2, params).fetchall(), columns=["sede", "cantidad"])

        query_g3 = text(f"SELECT SEDE as sede, COALESCE(SUM(GRUPO_3), 0) as cantidad FROM {table_name} WHERE FECHA = :year AND SEDE IS NOT NULL AND SEDE != '' AND SEDE != 'SIN INFORMACION' GROUP BY sede ORDER BY cantidad DESC")
        df_g3 = pd.DataFrame(connection.execute(query_g3, params).fetchall(), columns=["sede", "cantidad"])

        return df_g1, df_g2, df_g3, total_matriculados, total_grupo1, total_grupo2, total_grupo3

# --- Consultas y Visualización Principal ---
try:
    df_grupo1, df_grupo2, df_grupo3, total_matriculados, total_grupo1, total_grupo2, total_grupo3 = load_escuela_nueva_data(engine, selected_year)

    # Calcular estadísticas para la barra lateral
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Matriculados ({selected_year})", f"{int(total_matriculados):,}")
    st.sidebar.metric(f"Matriculados Grupo 1 ({selected_year})", f"{int(total_grupo1):,}")
    st.sidebar.metric(f"Matriculados Grupo 2 ({selected_year})", f"{int(total_grupo2):,}")
    st.sidebar.metric(f"Matriculados Grupo 3 ({selected_year})", f"{int(total_grupo3):,}")
    st.sidebar.divider()
    
    # Layout de tres columnas
    col1, col2, col3 = st.columns(3)
    with col1:
        create_bar_chart_and_table(df_grupo1, total_grupo1, f"📊 Grupo 1 - Año {selected_year}")
    with col2:
        create_bar_chart_and_table(df_grupo2, total_grupo2, f"📊 Grupo 2 - Año {selected_year}")
    with col3:
        create_bar_chart_and_table(df_grupo3, total_grupo3, f"📊 Grupo 3 - Año {selected_year}")
    
    # --- Selección de Año con Botones ---
    st.divider()
    with st.expander("📅 **Seleccionar Año para Visualizar**", expanded=True):
        st.write("Haz clic en un botón para cambiar el año de los datos mostrados.")
        
        cols = st.columns(len(available_years))
        def set_year(year):
            st.session_state.selected_year = year

        for i, year in enumerate(available_years):
            with cols[i]:
                button_type = "primary" if year == selected_year else "secondary"
                st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)