import sys
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env para desarrollo local
load_dotenv()

def get_engine():
    """
    Crea y devuelve una instancia del motor de SQLAlchemy.
    Lee las credenciales de las variables de entorno (o de st.secrets en producción).
    """
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')

    connection_string = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string)
    return engine

# Crear instancia global del engine para uso en otros módulos
engine = get_engine()
