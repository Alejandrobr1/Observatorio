import streamlit as st
import os
import sys
import subprocess
import webbrowser
import socket
import io
import zipfile
import pandas as pd
from sqlalchemy import create_engine, text, inspect

# Página principal que lanza los otros dashboards y permite exportar la BD a CSV(s)

st.set_page_config(layout="wide", page_title="Panel Principal - Dashboards")
st.title("📌 Panel Principal - Dashboards del Observatorio")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))

# Rutas a los scripts de dashboards (relativas a este archivo)
DASHBOARDS = {
    'Estudiantes por Sexo y Grado': os.path.join(ROOT, 'estudiantes_grado_sexo.py'),
    'Asistencia por Institución': os.path.join(ROOT, 'asistencia_institucion.py'),
    'Estudiantes por Nivel MCER': os.path.join(ROOT, 'estudiantes_niveles.py'),
    'Aprobación de Estudiantes': os.path.join(ROOT, 'Estado_estudiantes.py')
}

# Puerto por defecto para lanzar cada dashboard si el usuario pulsa "Abrir"
DEFAULT_PORTS = [8501, 8502, 8503, 8504]

@st.cache_resource
def get_engine():
    # Ajusta la cadena de conexión si fuera necesario
    return create_engine("mysql+mysqlconnector://root:123456@localhost:3308/observatorio_bilinguismo")

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True

def start_streamlit(script_path: str, port: int):
    """Start a streamlit process for the given script on the given port in background."""
    # If already in session state, don't start again
    servers = st.session_state.get('servers', {})
    if script_path in servers:
        proc = servers[script_path]
        if proc.poll() is None:
            return port, proc

    cmd = [sys.executable, '-m', 'streamlit', 'run', script_path, '--server.port', str(port), '--server.headless', 'true']
    # Start process in background
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        st.error(f"No se pudo iniciar el servidor Streamlit: {e}")
        return None, None

    # store
    servers[script_path] = proc
    st.session_state['servers'] = servers
    return port, proc

def export_all_tables_to_zip(engine):
    """Export all tables in the current database to a zip file (each table as a csv). Returns bytes."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for table in tables:
            try:
                df = pd.read_sql(text(f"SELECT * FROM `{table}`"), engine)
            except Exception:
                # skip tables that cannot be read
                continue

            csv_bytes = df.to_csv(index=False).encode('utf-8')
            zf.writestr(f"{table}.csv", csv_bytes)

    mem_zip.seek(0)
    return mem_zip.read()


st.markdown(
    "Selecciona uno de los dashboards para abrirlo o usa el botón de exportar para descargar la base de datos completa en un ZIP con CSVs por tabla."
)

cols = st.columns(4)
for i, (label, path) in enumerate(DASHBOARDS.items()):
    with cols[i % 4]:
        if st.button(f"Abrir: {label}"):
            # Find a free port among defaults
            chosen_port = None
            for p in DEFAULT_PORTS:
                if not is_port_in_use(p):
                    chosen_port = p
                    break
            if chosen_port is None:
                st.warning("No hay puertos libres en la lista de puertos. Elige uno manualmente en la configuración.")
            else:
                port, proc = start_streamlit(path, chosen_port)
                if proc is not None:
                    url = f"http://localhost:{port}"
                    st.success(f"Servidor iniciado en {url} (script: {os.path.basename(path)})")
                    # Intentar abrir el navegador
                    try:
                        webbrowser.open(url)
                    except Exception:
                        pass

st.divider()

st.header("Exportar base de datos")
st.write("Descarga un ZIP que contiene un CSV por cada tabla de la base de datos.")

engine = get_engine()

if st.button("📥 Exportar DB a ZIP (CSV por tabla)"):
    with st.spinner("Generando exportación, esto puede tardar unos segundos..."):
        try:
            data_bytes = export_all_tables_to_zip(engine)
            st.success("Exportación lista")
            st.download_button("Descargar ZIP con CSVs", data=data_bytes, file_name="observatorio_export.zip", mime="application/zip")
        except Exception as e:
            st.error(f"Error al exportar la base de datos: {e}")

st.info("Nota: Los dashboards se lanzan en procesos Streamlit separados en puertos locales. Si ya tienes instancias corriendo, puede que el puerto esté ocupado; el script intentará usar los puertos 8501-8504.")
