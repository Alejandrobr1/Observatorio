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
            ("2p-estudiantes_por_poblacion.py", "Matriculados por Población", "👥"),
            ("3p-estudiantes_por_sede_nodal_etapa1_2.py", "“Participación % por sede nodal", "⚖️"),
            ("4p-estudiantes_por_sede_nodal_barras_etp1_2.py", "Matriculados por sede nodal", "📊"),
            ("5p-estudiantes_por_institucion.py", "Estudiantes por Institución (Escuela Nueva)", "🏛️"),
        ],
        "first_page": "1p-estudiantes_por_jornada_dia.py"
    },
    DOCENTES_LABEL: {
        "pages": [
            ("6p-docentes_por_nivel.py", "Docentes por Nivel MCER", "🎓"),
            ("7p-docentes_por_institucion.py", "Docentes por Institución", "🏫"),
        ],
        "first_page": "6p-docentes_por_nivel.py",
        
    },
    COLOMBO_LABEL: {
        "pages": [
            ("8p-colombo_por_institucion.py", "Colombo - Estudiantes por Institución", "🏫"),
            ("9p-colombo_por_nivel.py", "Colombo - Estudiantes por Nivel", "📈"),
        ],
        "first_page": "8p-colombo_por_institucion.py",
        
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
    Initialize the filter based on current page only if not already set.
    This allows the filter to be set when first visiting a page, but respects
    user changes afterward.
    """
    # This function is now a no-op - filter is managed by user selection
    # and initial page context
    pass

def create_nav_buttons(selected_pop):
    # Filtro de población en la parte superior
    col_selector = st.columns([2, 5])
    with col_selector[0]:
        new_pop = st.selectbox(
            "Población:",
            options=list(DASHBOARD_CATEGORIES.keys()),
            index=list(DASHBOARD_CATEGORIES.keys()).index(selected_pop),
            key="population_selector"
        )
        if new_pop != selected_pop:
            st.session_state.population_filter = new_pop
            st.rerun()
    
    # Botones de navegación con máximo 3 por fila
    if selected_pop in DASHBOARD_CATEGORIES:
        pages = DASHBOARD_CATEGORIES[selected_pop]["pages"]
        all_buttons = [("app.py", "Inicio", "🏠")] + [(f"pages/{pf}", label, icon) for pf, label, icon in pages]
        
        # Primera fila: máximo 3 botones
        first_row = all_buttons[:3]
        nav_cols_1 = st.columns(len(first_row))
        for i, (page_path, label, icon) in enumerate(first_row):
            with nav_cols_1[i]:
                st.page_link(page_path, label=label, icon=icon)
        
        # Segunda fila: botones restantes (a partir del cuarto)
        if len(all_buttons) > 3:
            second_row = all_buttons[3:]
            nav_cols_2 = st.columns(len(second_row))
            for i, (page_path, label, icon) in enumerate(second_row):
                with nav_cols_2[i]:
                    st.page_link(page_path, label=label, icon=icon)




