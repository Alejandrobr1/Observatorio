# Configuración compartida para navegación de dashboards
# Este archivo define las constantes y funciones utilizadas en toda la aplicación
import streamlit as st

COMFENALCO_LABEL = "Formación a estudiantes Comfenalco Antioquia"
DOCENTES_LABEL = "Formación a docentes"
COLOMBO_LABEL = "Formación a estudiantes Centro Colombo Americano de Medellín"

# Mapeo de categorías a páginas
DASHBOARD_CATEGORIES = {
    COMFENALCO_LABEL: {
        "pages": [
            ("1p-estudiantes_por_jornada_dia.py", "Matriculados por Jornada y Día", "📅"),
            ("2p-estudiantes_por_poblacion.py", "Matriculados por Tipo de Población", "👥"),
            ("3p-estudiantes_por_sede_nodal_etapa1_2.py", "Comparativa Etapas por Sede (Pastel)", "⚖️"),
            ("4p-estudiantes_por_sede_nodal_barras_etp1_2.py", "Comparativa Etapas por Sede (Barras)", "📊"),
            ("5p-estudiantes_por_institucion.py", "Estudiantes por Institución (Escuela Nueva)", "🏛️"),
        ],
        "first_page": "1p-estudiantes_por_jornada_dia.py"
    },
    DOCENTES_LABEL: {
        "pages": [
            ("6p-docentes_por_nivel.py", "Docentes por Nivel MCER", "🎓"),
            ("7p-docentes_por_institucion.py", "Docentes por Institución", "🏫"),
        ],
        "first_page": "6p-docentes_por_nivel.py"
    },
    COLOMBO_LABEL: {
        "pages": [
            ("8p-colombo_por_institucion.py", "Colombo - Estudiantes por Institución", "🏫"),
            ("9p-colombo_por_nivel.py", "Colombo - Estudiantes por Nivel", "📈"),
        ],
        "first_page": "8p-colombo_por_institucion.py"
    }
}

def get_current_page_category(current_page_file):
    """
    Determine the category of the current page based on its filename.
    Returns the category label (COMFENALCO_LABEL, DOCENTES_LABEL, or COLOMBO_LABEL)
    or None if not found.
    """
    for category, config in DASHBOARD_CATEGORIES.items():
        for page_file, _, _ in config["pages"]:
            if current_page_file in page_file or page_file in current_page_file:
                return category
    return None


def update_filter_by_page(current_page_file):
    """
    Update the population_filter in session_state based on the current page.
    This ensures the filter always matches the active page's category.
    """
    category = get_current_page_category(current_page_file)
    if category and st.session_state.population_filter != category:
        st.session_state.population_filter = category


def create_nav_buttons(selected_pop):
    """
    Create navigation buttons for the selected population category.
    Only displays pages belonging to the selected population.
    """
    nav_cols = st.columns(8)
    with nav_cols[0]:
        st.page_link("app.py", label="Inicio", icon="🏠")
    
    # Get pages for the selected population category
    if selected_pop in DASHBOARD_CATEGORIES:
        pages = DASHBOARD_CATEGORIES[selected_pop]["pages"]
        for i, (page_file, label, icon) in enumerate(pages):
            with nav_cols[i + 1]:
                st.page_link(f"pages/{page_file}", label=label, icon=icon)
