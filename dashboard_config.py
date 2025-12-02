# Configuración compartida para navegación de dashboards
# Este archivo define las constantes y funciones utilizadas en toda la aplicación
import streamlit as st

COMFENALCO_LABEL = "Comfenalco Antioquia"
COLOMBO_LABEL = "Centro Colombo Americano Medellín"

# Mapeo de categorías y subcategorías a páginas
DASHBOARD_CATEGORIES = {
    COMFENALCO_LABEL: {
        "subcategories": {
            "Años 2016 al 2019": [
                ("1p-estudiantes_por_jornada_dia.py", "Estudiantes por Jornada y día", "📅"),
                ("2p-estudiantes_por_poblacion.py", "Estudiantes por Población", "👥"),
                ("3p-estudiantes_por_sede_nodal_etapa1_2.py", "Participación % por Sede nodal", "⚖️"),
                ("4p-estudiantes_por_sede_nodal_barras_etp1_2.py", "Estudiantes por Sede nodal", "📊"),
                ("5p-estudiantes_por_institucion.py", "Estudiantes Escuela Nueva", "🏫"),
            ],
            "Años 2021 al 2025": [
                ("10p-estudiantes_por_institucion_2021_2025.py", "Estudiantes por Institución Educativa", "🏫"),
                ("11p-estudiantes_por_grado_2021_2025.py", "Estudiantes por Grado", "🎓"),
            ],
            "Intensificación lingüística": [
                ("12p-estudiantes_por_institucion_intensificacion.py", "Estudiantes por Institución", "🏫"),
                ("13p-estudiantes_por_grado_intensificacion.py", "Estudiantes por Grado", "🎓"),
                ("14p-estudiantes_por_idioma_intensificacion.py", "Estudiantes por Idioma", "📈"),
            ]
        }
    },
   
    COLOMBO_LABEL: {
        "subcategories": {
            "Formación a estudiantes": [
                ("8p-colombo_por_institucion.py", "Estudiantes por Institución Educativa", "🏫"),
                ("9p-colombo_por_nivel.py", "Estudiantes por nivel MCER", "📈"),
            ],
            "Formación a docentes": [
                ("6p-docentes_por_nivel.py", "Docentes por nivel MCER", "🎓"),
                ("7p-docentes_por_institucion.py", "Docentes por Institución Educativa", "🏫"),
            ]
        }
    }
}

def get_current_page_category(current_page_file):
    """
    Determine the category of the current page based on its filename.
    Returns the category label (COMFENALCO_LABEL, DOCENTES_LABEL, or COLOMBO_LABEL)
    or None if not found.
    """
    for category, config in DASHBOARD_CATEGORIES.items():
        if "subcategories" in config:
            for sub_pages in config["subcategories"].values():
                for page_file, _, _ in sub_pages:
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
    # Inicializar estados de sesión si no existen
    if 'comfenalco_subcategory' not in st.session_state:
        st.session_state.comfenalco_subcategory = "Años 2016 al 2019"
    if 'colombo_subcategory' not in st.session_state:
        st.session_state.colombo_subcategory = "Formación a estudiantes"

    # Botones de categoría principal
    with st.container(border=False):
        st.markdown('<div class="main-category-btns">', unsafe_allow_html=True)
        pop_options = [COMFENALCO_LABEL, COLOMBO_LABEL]
        cols_pop = st.columns(len(pop_options))
        
        def set_population(pop_type):
            st.session_state.population_filter = pop_type

        for i, pop in enumerate(pop_options):
            with cols_pop[i]:
                st.button(pop, key=f"pop_btn_{pop}_nav", on_click=set_population, args=(pop,), use_container_width=True, type="primary" if selected_pop == pop else "secondary")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Botones de subcategoría y enlaces
    if selected_pop in DASHBOARD_CATEGORIES:
        category_config = DASHBOARD_CATEGORIES[selected_pop]
        subcategories = list(category_config["subcategories"].keys())
        
        # Determinar y gestionar la subcategoría activa
        if selected_pop == COMFENALCO_LABEL:
            active_subcategory = st.session_state.comfenalco_subcategory
            def set_sub(sub):
                st.session_state.comfenalco_subcategory = sub
        else: # COLOMBO_LABEL
            active_subcategory = st.session_state.colombo_subcategory
            def set_sub(sub):
                st.session_state.colombo_subcategory = sub

        # Mostrar botones de subcategoría
        with st.container(border=False):
            st.markdown('<div class="subcategory-btns">', unsafe_allow_html=True)
            cols_sub = st.columns(len(subcategories))
            for i, sub in enumerate(subcategories):
                with cols_sub[i]:
                    st.button(sub, key=f"sub_btn_{sub}_nav", on_click=set_sub, args=(sub,), use_container_width=True, type="primary" if active_subcategory == sub else "secondary")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Mostrar enlaces de la subcategoría activa
        pages = category_config["subcategories"].get(active_subcategory, [])
        all_buttons = [("app.py", "Inicio", "🏠")] + [(f"pages/{pf}", label, icon) for pf, label, icon in pages]
    
        # Dividir botones en grupos de 2 para un layout más limpio
        for i in range(0, len(all_buttons), 2):
            row_buttons = all_buttons[i:i+2]
            nav_cols = st.columns(2)
            for j, (page_path, label, icon) in enumerate(row_buttons):
                with nav_cols[j]:
                    st.page_link(page_path, label=label, icon=icon, use_container_width=True)
