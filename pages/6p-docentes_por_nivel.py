import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import traceback
from sqlalchemy import create_engine, text
import sys
import os
from app import COMFENALCO_LABEL, DOCENTES_LABEL, COLOMBO_LABEL
# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar streamlit
st.set_page_config(layout="wide", page_title="Docentes por Nivel MCER")
st.title("📊 Docentes por Nivel MCER")

# --- State and Navigation ---
if 'population_filter' not in st.session_state:
    st.session_state.population_filter = "Docentes"

def create_nav_buttons(selected_pop):
    nav_cols = st.columns(8)
    with nav_cols[0]:
        st.page_link("app.py", label="Inicio", icon="🏠")

    if selected_population != COMFENALCO_LABEL:
        links = {
            "Jornada/Día": "pages/1p-estudiantes_por_jornada_dia.py",
            "Población": "pages/2p-estudiantes_por_poblacion.py",
            "Participación % por sede nodal": "pages/3p-estudiantes_por_sede_nodal_etapa1_2.py",
            "Matriculados por sede nodal": "pages/4p-estudiantes_por_sede_nodal_barras_etp1_2.py",
            "Estudiantes por institución\n(Escuela nueva)": "pages/5p-estudiantes_por_institucion.py"
        }
        # Re-ajustar columnas para acomodar todos los botones
        nav_cols = st.columns(len(links) + 1)
        with nav_cols[0]:
            st.page_link("app.py", label="Inicio", icon="🏠")
        for i, (label, page) in enumerate(links.items()):
            with nav_cols[i+1]:
                st.page_link(page, label=label)

    elif selected_pop == DOCENTES_LABEL:
        with nav_cols[1]:
            st.page_link("pages/6p-docentes_por_nivel.py", label="Docentes por Nivel", icon="🎓")
        with nav_cols[2]:
            st.page_link("pages/7p-docentes_por_institucion.py", label="Docentes por Institución", icon="🏫")

    elif selected_pop == COLOMBO_LABEL:
        with nav_cols[1]:
            st.page_link("pages/8p-colombo_por_institucion.py", label="Colombo por Institución", icon="🏫")
        with nav_cols[2]:
            st.page_link("pages/9p-colombo_por_nivel.py", label="Colombo por Nivel", icon="📈")

create_nav_buttons(st.session_state.population_filter)
st.markdown("---")
st.markdown("""
<style>
    /* Style for page links */
    a[data-testid="stPageLink"] {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 8px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        height: 4.5em; /* Altura fija para todos los botones */
        line-height: 1.2; /* Espaciado para texto en varias líneas */
        word-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

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
except Exception as e:
    st.error("❌ No se pudo conectar a la base de datos")
    st.exception(e)
    st.stop()

@st.cache_data
def get_available_years(_engine):
    table_name = "Docentes"
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

# Función para generar gráfico de dona y tabla
def create_donut_chart_and_table(df_data, total_docentes, title):
    st.header(f"📊 {title} - Año {st.session_state.selected_year}")
    
    if df_data.empty:
        st.warning("No hay datos de docentes para el año seleccionado.")
        return

    df_data['cantidad'] = pd.to_numeric(df_data['cantidad'])
    df_data = df_data[df_data['cantidad'] > 0]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Resumen por Nivel")
        df_data['porcentaje'] = (df_data['cantidad'] / float(total_docentes) * 100) if total_docentes > 0 else 0
        df_display = df_data.copy()
        df_display['#'] = range(1, len(df_display) + 1)
        df_display['cantidad'] = df_display['cantidad'].apply(lambda x: f"{int(x):,}")
        df_display['porcentaje'] = df_display['porcentaje'].apply(lambda x: f"{x:.2f}%")
        df_display = df_display[['#', 'NIVEL', 'cantidad', 'porcentaje']]
        df_display.columns = ['#', 'Nivel', 'Docentes', 'Porcentaje']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Visualización")
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Gráfico de Dona
        labels = df_data['NIVEL']
        sizes = df_data['cantidad']
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(labels)))
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                          colors=colors, pctdistance=0.85,
                                          wedgeprops=dict(width=0.4, edgecolor='w'))
        
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.set_title("Distribución de Docentes por Nivel", pad=20)
        
        # Círculo central para hacer la dona
        centre_circle = plt.Circle((0,0),0.60,fc='white')
        fig.gca().add_artist(centre_circle)
        
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.tight_layout()
        st.pyplot(fig)
        
@st.cache_data
def load_data(_engine, year):
    table_name = "Docentes"
    with _engine.connect() as connection:
        if not _engine.dialect.has_table(connection, table_name):
            return pd.DataFrame(), 0, 0
        
        params = {'year': year}
        query_data = text(f"""
            SELECT 
                NIVEL, COUNT(ID) as cantidad
            FROM {table_name}
            WHERE FECHA = :year
              AND NIVEL IS NOT NULL 
              AND NIVEL != '' 
              AND NIVEL != 'SIN INFORMACION'
            GROUP BY NIVEL
            ORDER BY cantidad DESC
        """)
        df = pd.DataFrame(connection.execute(query_data, params).fetchall(), columns=["NIVEL", "cantidad"])
        
        query_total = text(f"SELECT COUNT(ID) FROM {table_name} WHERE FECHA = :year")
        total_docentes = connection.execute(query_total, params).scalar() or 0
        
        query_instituciones = text(f"SELECT COUNT(DISTINCT INSTITUCION_EDUCATIVA) FROM {table_name} WHERE FECHA = :year")
        total_instituciones = connection.execute(query_instituciones, params).scalar() or 0
        
        return df, total_docentes, total_instituciones

try:
    st.sidebar.header("Filtros")
    selected_population = st.sidebar.selectbox(
        "Filtrar por tipo de población",
        [COMFENALCO_LABEL, COLOMBO_LABEL, DOCENTES_LABEL],
        index=[COMFENALCO_LABEL, COLOMBO_LABEL, DOCENTES_LABEL].index(st.session_state.population_filter),
        key="population_filter",
        help="Selecciona el grupo de datos a visualizar."
    )
    st.sidebar.divider()

    if selected_population != DOCENTES_LABEL:
        st.info(f"Este dashboard es para {DOCENTES_LABEL}. Por favor, selecciona esa opción en el filtro de población para ver los datos.")
        st.stop()

    available_years = get_available_years(engine)
    if not available_years:
        st.warning(f"⚠️ No se encontraron datos para {DOCENTES_LABEL}.")
        st.stop()

    if 'selected_year' not in st.session_state or st.session_state.selected_year not in available_years:
        st.session_state.selected_year = available_years[0]
    selected_year = st.session_state.selected_year

    df_docentes, total_docentes, total_instituciones = load_data(engine, selected_year)

    st.sidebar.info(f"**Año:** {selected_year}")
    st.sidebar.divider()
    st.sidebar.header("📈 Estadísticas Generales")
    st.sidebar.metric(f"Total Docentes ({selected_year})", f"{int(total_docentes):,}")
    st.sidebar.metric(f"Instituciones con Docentes ({selected_year})", f"{int(total_instituciones):,}")
    st.sidebar.divider()
    # Añadir el logo al final del sidebar
    if os.path.exists("assets/Logo_rionegro.png"):
        st.sidebar.image("assets/Logo_rionegro.png")

    # Layout en dos columnas: Gráfico y tabla a la izquierda, filtro de año a la derecha
    col1, col2 = st.columns([3, 1])

    with col1:
        create_donut_chart_and_table(df_docentes, total_docentes, "Distribución de Docentes por Nivel")

    with col2:
        st.write("📅 **Seleccionar Año**")
        def set_year(year):
            st.session_state.selected_year = year
        for year in available_years:
            button_type = "primary" if year == selected_year else "secondary"
            st.button(str(year), key=f"year_{year}", use_container_width=True, type=button_type, on_click=set_year, args=(year,))

except Exception as e:
    st.error("❌ Error al cargar los datos")
    st.exception(e)

def add_interest_links():
    st.markdown("---")
    st.markdown("### 🔗 Enlaces de Interés")
    st.markdown("""
    - [Agencia Pública de Empleo Municipio de Comfenalco](https://www.comfenalcoantioquia.com.co/personas/sedes/oficina-de-empleo-oriente)
     - [Agencia Pública de Empleo Municipio de Rionegro](https://www.comfenalcoantioquia.com.co/personas/servicios/agencia-de-empleo/ofertas)
     - [Agencia Pública de Empleo SENA](https://ape.sena.edu.co/Paginas/Inicio.aspx) 
    """)
add_interest_links()
