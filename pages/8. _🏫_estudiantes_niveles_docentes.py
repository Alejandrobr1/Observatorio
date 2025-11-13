"""
Dashboard: Docentes por Nivel MCER y Sexo - Formación Docente
"""
import streamlit as st
import os
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


st.set_page_config(page_title="MCER por Sexo - Docentes", layout="wide", page_icon="📊")


st.title("📊 Docentes por Nivel MCER y Sexo - Formación Docente")


@st.cache_resource
def get_engine():
    try:
        db_user = st.secrets.get("DB_USER", os.getenv('DB_USER', 'root'))
        db_pass = st.secrets.get("DB_PASS", os.getenv('DB_PASS', '123456'))
        db_host = st.secrets.get("DB_HOST", os.getenv('DB_HOST', 'localhost'))
        db_port = st.secrets.get("DB_PORT", os.getenv('DB_PORT', '3308'))
        db_name = st.secrets.get("DB_NAME", os.getenv('DB_NAME', 'observatorio_bilinguismo'))
    except FileNotFoundError:
        db_user = os.getenv('DB_USER', 'root')
        db_pass = os.getenv('DB_PASS', '123456')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '3308')
        db_name = os.getenv('DB_NAME', 'observatorio_bilinguismo')
    
    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)


try:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    st.sidebar.success("✅ Conexión establecida")
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()


st.sidebar.header("🔍 Filtros")


with engine.connect() as connection:
    query_years = text("""
        SELECT DISTINCT pnm.ANIO_REGISTRO as año
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        WHERE pnm.ANIO_REGISTRO IS NOT NULL
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion docente%'
        AND p.TIPO_PERSONA = 'Docente'
        AND pnm.ANIO_REGISTRO BETWEEN 2016 AND 2025
        ORDER BY año DESC
    """)
    result_years = connection.execute(query_years)
    available_years = [str(int(row[0])) for row in result_years.fetchall() if row[0]]


    if not available_years:
        st.warning("⚠️ No hay datos de Formación Docente disponibles")
        st.stop()


    selected_year = st.sidebar.selectbox('📅 Año', available_years, index=0)


with engine.connect() as connection:
    query = text("""
        SELECT 
            n.NIVEL_MCER,
            p.SEXO,
            COUNT(DISTINCT p.NUMERO_DOCUMENTO) as cantidad
        FROM Persona_Nivel_MCER pnm
        INNER JOIN Personas p ON pnm.PERSONA_ID = p.ID
        INNER JOIN Nivel_MCER n ON pnm.NIVEL_MCER_ID = n.ID
        WHERE pnm.ANIO_REGISTRO = :year
        AND LOWER(pnm.NOMBRE_CURSO) LIKE '%formacion docente%'
        AND p.TIPO_PERSONA = 'Docente'
        AND n.NIVEL_MCER IS NOT NULL
        AND n.NIVEL_MCER != 'SIN INFORMACION'
        AND p.SEXO IS NOT NULL
        AND p.SEXO != ''
        AND p.SEXO != 'SIN INFORMACION'
        GROUP BY n.NIVEL_MCER, p.SEXO
        ORDER BY n.NIVEL_MCER, p.SEXO
    """)
    
    result = connection.execute(query, {"year": int(selected_year)})
    data = result.fetchall()


if data:
    df = pd.DataFrame(data, columns=['Nivel_MCER', 'Sexo', 'Cantidad'])
    
    # Normalizar valores de sexo
    df['Sexo_Normalizado'] = df['Sexo'].str.upper().apply(
        lambda x: 'Masculino' if any(term in x for term in ['M', 'MASCULINO', 'HOMBRE']) 
        else ('Femenino' if any(term in x for term in ['F', 'FEMENINO', 'MUJER']) else 'Otro')
    )
    
    # Agrupar por nivel y sexo normalizado
    df_grouped = df.groupby(['Nivel_MCER', 'Sexo_Normalizado'])['Cantidad'].sum().reset_index()
    
    # Crear pivot table para facilitar cálculos
    df_pivot = df_grouped.pivot_table(
        index='Nivel_MCER', 
        columns='Sexo_Normalizado', 
        values='Cantidad', 
        fill_value=0
    ).reset_index()
    
    # Calcular totales
    total_masculino = df_grouped[df_grouped['Sexo_Normalizado'] == 'Masculino']['Cantidad'].sum()
    total_femenino = df_grouped[df_grouped['Sexo_Normalizado'] == 'Femenino']['Cantidad'].sum()
    total_general = total_masculino + total_femenino
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Docentes", int(total_general))
    with col2:
        st.metric("👨 Total Masculino", int(total_masculino))
    with col3:
        st.metric("👩 Total Femenino", int(total_femenino))
    with col4:
        porcentaje_fem = (total_femenino / total_general * 100) if total_general > 0 else 0
        st.metric("📈 % Femenino", f"{porcentaje_fem:.1f}%")
    
    st.divider()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras apiladas
        fig_stacked = go.Figure()
        
        masculino_vals = [df_pivot[df_pivot['Nivel_MCER'] == nivel]['Masculino'].values[0] 
                         if 'Masculino' in df_pivot.columns and len(df_pivot[df_pivot['Nivel_MCER'] == nivel]) > 0
                         else 0 
                         for nivel in df_pivot['Nivel_MCER']]
        
        femenino_vals = [df_pivot[df_pivot['Nivel_MCER'] == nivel]['Femenino'].values[0] 
                        if 'Femenino' in df_pivot.columns and len(df_pivot[df_pivot['Nivel_MCER'] == nivel]) > 0
                        else 0 
                        for nivel in df_pivot['Nivel_MCER']]
        
        fig_stacked.add_trace(go.Bar(
            name='Masculino',
            x=df_pivot['Nivel_MCER'],
            y=masculino_vals,
            marker_color='#3498db',
            text=masculino_vals,
            textposition='inside',
            texttemplate='%{text}',
            hovertemplate='<b>%{x}</b><br>Masculino: %{y}<extra></extra>'
        ))
        
        fig_stacked.add_trace(go.Bar(
            name='Femenino',
            x=df_pivot['Nivel_MCER'],
            y=femenino_vals,
            marker_color='#e74c3c',
            text=femenino_vals,
            textposition='inside',
            texttemplate='%{text}',
            hovertemplate='<b>%{x}</b><br>Femenino: %{y}<extra></extra>'
        ))
        
        fig_stacked.update_layout(
            title=f"Distribución por Nivel MCER y Sexo - {selected_year}",
            barmode='stack',
            xaxis_title='Nivel MCER',
            yaxis_title='Cantidad de Docentes',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        
        st.plotly_chart(fig_stacked, use_container_width=True)
    
    with col2:
        # Gráfico de pastel por sexo
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Masculino', 'Femenino'],
            values=[total_masculino, total_femenino],
            marker=dict(colors=['#3498db', '#e74c3c']),
            textinfo='label+percent+value',
            hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        )])
        
        fig_pie.update_layout(
            title=f"Distribución por Sexo - {selected_year}",
            height=500
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Tabla detallada
    st.subheader("📋 Datos Detallados por Nivel MCER")
    
    # Preparar tabla con totales
    tabla_resumen = []
    for nivel in sorted(df_pivot['Nivel_MCER'].unique()):
        nivel_data = df_pivot[df_pivot['Nivel_MCER'] == nivel]
        masc = int(nivel_data['Masculino'].values[0]) if 'Masculino' in df_pivot.columns and len(nivel_data) > 0 else 0
        fem = int(nivel_data['Femenino'].values[0]) if 'Femenino' in df_pivot.columns and len(nivel_data) > 0 else 0
        total_nivel = masc + fem
        porcentaje = (total_nivel / total_general * 100) if total_general > 0 else 0
        
        tabla_resumen.append({
            'Nivel MCER': nivel,
            'Masculino': masc,
            'Femenino': fem,
            'Total': total_nivel,
            'Porcentaje': f"{porcentaje:.1f}%"
        })
    
    # Agregar fila de totales
    tabla_resumen.append({
        'Nivel MCER': 'TOTAL',
        'Masculino': int(total_masculino),
        'Femenino': int(total_femenino),
        'Total': int(total_general),
        'Porcentaje': '100.0%'
    })
    
    df_tabla = pd.DataFrame(tabla_resumen)
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
    
    # Gráfico adicional: Distribución por nivel
    st.subheader("📊 Comparación por Nivel MCER")
    
    df_pivot['Total'] = df_pivot.get('Masculino', 0) + df_pivot.get('Femenino', 0)
    
    fig_total = px.bar(
        df_pivot.sort_values('Total', ascending=True),
        y='Nivel_MCER',
        x='Total',
        orientation='h',
        title=f"Total de Docentes por Nivel MCER - {selected_year}",
        color='Total',
        color_continuous_scale='viridis',
        labels={'Total': 'Total Docentes', 'Nivel_MCER': 'Nivel MCER'},
        text='Total'
    )
    
    fig_total.update_traces(texttemplate='%{text}', textposition='outside')
    fig_total.update_layout(height=400)
    
    st.plotly_chart(fig_total, use_container_width=True)
    
    # Datos originales en expander
    with st.expander("🔍 Ver datos originales sin procesar"):
        st.dataframe(df.sort_values(['Nivel_MCER', 'Sexo']), use_container_width=True, hide_index=True)
    
    st.success(f"""
    ✅ **Datos cargados exitosamente**
    
    📌 **Información del reporte:**
    - **Curso**: Formación Docente
    - **Tipo de población**: Docente
    - **Año**: {selected_year}
    - **Total docentes**: {int(total_general):,}
    - **Niveles MCER**: {', '.join(sorted(df_pivot['Nivel_MCER'].unique()))}
    """)

else:
    st.warning(f"⚠️ No hay datos de MCER por Sexo para Docentes en el año {selected_year}")
